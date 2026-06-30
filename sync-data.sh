#!/usr/bin/env bash
# ============================================================
# Quant-UI 数据同步脚本 (在本地机器上运行)
# ============================================================
# 将本地 CSV 数据文件同步到 Linux 服务器
# 支持 rsync (增量同步) 和 scp (全量复制) 两种方式
#
# 用法:
#   ./sync-data.sh user@server-ip
#   ./sync-data.sh user@server-ip /path/to/local/data
#   ./sync-data.sh user@server-ip /path/to/local/data /remote/data/path
#
# 环境变量:
#   REMOTE_DATA_DIR  远程数据目录 (默认 /home/ubuntu/quant-ui-data)
#   LOCAL_DATA_DIR   本地数据目录
#
# 示例:
#   ./sync-data.sh root@192.168.1.100                          # 自动检测本地数据目录
#   ./sync-data.sh root@192.168.1.100 /d/github/RobotMeQ_Dataset/QuantData
# ============================================================
set -uo pipefail

# ── 颜色 ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo ""
echo -e "${CYAN}========================================="
echo " Quant-UI 数据同步"
echo -e "=========================================${NC}"
echo ""

# ── 1. 解析参数 ──────────────────────────────────────────
if [ $# -lt 1 ]; then
    echo "用法: $0 <user@host> [本地数据目录] [远程数据目录]"
    echo ""
    echo "示例:"
    echo "  $0 root@192.168.1.100"
    echo "  $0 root@192.168.1.100 /d/github/RobotMeQ_Dataset/QuantData"
    echo "  $0 root@192.168.1.100 /d/github/RobotMeQ_Dataset/QuantData /home/ubuntu/quant-ui-data"
    echo ""
    exit 1
fi

REMOTE="${1}"
LOCAL_DIR="${2:-}"
REMOTE_DIR="${3:-${REMOTE_DATA_DIR:-/home/ubuntu/quant-ui-data}}"

# 将 Windows 路径转为 Git Bash 可用的 Unix 路径
# D:/path → /d/path, D:\path → /d/path
_to_unix_path() {
    local p="$1"
    # 反斜杠 → 正斜杠
    p="${p//\\//}"
    # D: → /d, C: → /c
    if [[ "$p" =~ ^[A-Za-z]: ]]; then
        local drive
        drive=$(echo "${p:0:1}" | tr '[:upper:]' '[:lower:]')
        p="/${drive}${p:2}"
    fi
    # 确保以 / 开头
    [[ "$p" =~ ^/ ]] || p="/$p"
    # 移除末尾斜杠
    p="${p%/}"
    echo "$p"
}

# ── 2. 检测本地数据目录 ──────────────────────────────────
if [ -z "$LOCAL_DIR" ]; then
    # 尝试从 config.yaml 读取 price_root_dir
    if [ -f "config.yaml" ]; then
        detected_raw=$(grep -E '^[[:space:]]*price_root_dir:' config.yaml 2>/dev/null | head -1 | awk -F': ' '{print $2}' | tr -d '"' | tr -d "'" | sed 's/[[:space:]]*$//' || true)
        if [ -n "$detected_raw" ]; then
            detected=$(_to_unix_path "$detected_raw")
            if [ -d "$detected" ]; then
                # 如果 live_index, market_condition_live 等在上层目录，
                # 则用上级目录作为同步根，以便把这些子目录也包含进来
                if [ -d "$detected/live_index" ] || [ -d "$detected/market_condition_live" ]; then
                    LOCAL_DIR="$detected"
                elif [ -d "$(dirname "$detected")/live_index" ] || [ -d "$(dirname "$detected")/market_condition_live" ]; then
                    LOCAL_DIR="$(dirname "$detected")"
                    info "数据子目录在上层 $(basename "$LOCAL_DIR")，以 $LOCAL_DIR 为同步根"
                else
                    LOCAL_DIR="$detected"
                fi
                info "从 config.yaml 检测到数据目录: $LOCAL_DIR"
            fi
        fi
    fi

    # 尝试常见默认路径
    if [ -z "$LOCAL_DIR" ]; then
        for try_path in \
            "/d/github/RobotMeQ_Dataset/QuantData" \
            "/c/Users/${USER:-}/github/RobotMeQ_Dataset/QuantData" \
            "${HOME:-}/github/RobotMeQ_Dataset/QuantData"; do
            if [ -d "$try_path" ]; then
                LOCAL_DIR="$try_path"
                info "检测到数据目录: $LOCAL_DIR"
                break
            fi
        done
    fi

    # 手动输入
    if [ -z "$LOCAL_DIR" ]; then
        read -rp "请输入本地数据目录路径: " LOCAL_DIR
        LOCAL_DIR=$(_to_unix_path "$LOCAL_DIR")
    fi
fi

# 验证本地目录存在
if [ ! -d "$LOCAL_DIR" ]; then
    error "本地数据目录不存在: $LOCAL_DIR\n请确认 config.yaml 中的 price_root_dir 路径是否正确"
fi

# ── 3. 检测数据结构 ──────────────────────────────────────
# 判断价格文件是否在 live/ 子目录中
_PRICE_IN_LIVE=false
if ls "$LOCAL_DIR"/live/live_bar_*.csv >/dev/null 2>&1; then
    _PRICE_IN_LIVE=true
fi

# ── 4. 显示同步信息 ──────────────────────────────────────
echo ""
info "同步配置:"
echo "   本地目录:   $LOCAL_DIR"
echo "   远程地址:   $REMOTE"
echo "   远程目录:   $REMOTE_DIR"
echo ""

# 统计 CSV 文件
csv_count=$(
    cd "$LOCAL_DIR" 2>/dev/null || { echo 0; exit 0; }
    {
        if $_PRICE_IN_LIVE; then
            find ./live -maxdepth 1 -name 'live_bar_*.csv' -type f 2>/dev/null
        else
            find . -maxdepth 1 -name 'live_bar_*.csv' -type f 2>/dev/null
        fi
        find . -maxdepth 1 -name 'a800_stocks.csv' -type f 2>/dev/null
        find ./asset_code -maxdepth 1 -name 'a800_stocks.csv' -type f 2>/dev/null
        $_PRICE_IN_LIVE && find ./live -maxdepth 1 -name 'a800_stocks.csv' -type f 2>/dev/null
        find ./live_index -name '*.csv' -type f 2>/dev/null
        find ./market_condition_live -name '*.csv' -type f 2>/dev/null
        for d in ./trade_point_live_inference_*/; do
            [ -d "$d" ] && find "$d" -name '*.csv' -type f 2>/dev/null
        done
    } | wc -l
)
info "本地数据: $csv_count 个 CSV 文件 (仅策略信号/价格/指数/行情)"

read -rp "确认同步? [Y/n]: " confirm
if [ "$confirm" = "n" ] || [ "$confirm" = "N" ]; then
    info "已取消"
    exit 0
fi

# ── 4. 确保远程目录存在 ──────────────────────────────────
info "检查远程目录..."
ssh "$REMOTE" "mkdir -p $REMOTE_DIR/live_index $REMOTE_DIR/market_condition_live $REMOTE_DIR/output" || {
    error "无法连接到远程服务器，请检查 SSH 配置"
}

# 创建策略子目录 (根据远程已有的目录自动处理)
ssh "$REMOTE" "for d in $REMOTE_DIR/trade_point_live_inference_*/; do [ -d \"\$d\" ] || mkdir -p \"$REMOTE_DIR/trade_point_live_inference_fuzzy_ma\" \"$REMOTE_DIR/trade_point_live_inference_tea_radical_nature\"; done" 2>/dev/null || true

# ── 5. 同步数据 ──────────────────────────────────────────
# 只传输项目实际读取的目录和文件:
#   live_bar_*.csv / live/live_bar_*.csv   价格 K 线
#   a800_stocks.csv                        股票名称映射
#   live_index/                            指数行情
#   market_condition_live/                 行情分类
#   trade_point_live_inference_*/          策略信号

if command -v rsync >/dev/null 2>&1; then
    info "使用 rsync 增量同步 (只传输变化的文件)..."

    _do_rsync() {
        rsync -avzu --progress "$1" "$REMOTE:$REMOTE_DIR/$2" 2>&1 || {
            warn "rsync 失败: $1 → $REMOTE_DIR/$2"
        }
    }

    # 价格 K 线 (live/ 子目录下的文件提到根目录)
    if $_PRICE_IN_LIVE; then
        _do_rsync "$LOCAL_DIR/live/" ""
    else
        _do_rsync "$LOCAL_DIR/" ""
    fi

    # 指数行情
    [ -d "$LOCAL_DIR/live_index" ] && _do_rsync "$LOCAL_DIR/live_index/" "live_index/"

    # 行情分类
    [ -d "$LOCAL_DIR/market_condition_live" ] && _do_rsync "$LOCAL_DIR/market_condition_live/" "market_condition_live/"

    # 策略信号
    for _d in "$LOCAL_DIR"/trade_point_live_inference_*/; do
        [ -d "$_d" ] && _do_rsync "$_d" "$(basename "$_d")/"
    done

    # 股票名称映射 (可能在 asset_code/ 子目录，放到根目录)
    if [ -f "$LOCAL_DIR/asset_code/a800_stocks.csv" ]; then
        rsync -avzu "$LOCAL_DIR/asset_code/a800_stocks.csv" "$REMOTE:$REMOTE_DIR/a800_stocks.csv"
    fi
else
    info "rsync 不可用，使用 tar+ssh 传输..."
    cd "$LOCAL_DIR"

    # 生成文件列表到临时文件（避免管道缓冲问题）
    FILELIST="/tmp/quant-ui-sync-files.txt"
    {
        if $_PRICE_IN_LIVE; then
            find ./live -maxdepth 1 -name 'live_bar_*.csv' -type f 2>/dev/null
        else
            find . -maxdepth 1 -name 'live_bar_*.csv' -type f 2>/dev/null
        fi
        if $_PRICE_IN_LIVE; then
            find ./live -maxdepth 1 -name 'a800_stocks.csv' -type f 2>/dev/null
        fi
        find . -maxdepth 1 -name 'a800_stocks.csv' -type f 2>/dev/null
        find ./asset_code -maxdepth 1 -name 'a800_stocks.csv' -type f 2>/dev/null
        find ./live_index -name '*.csv' -type f 2>/dev/null
        find ./market_condition_live -name '*.csv' -type f 2>/dev/null
        for d in ./trade_point_live_inference_*/; do
            [ -d "$d" ] && find "$d" -name '*.csv' -type f 2>/dev/null
        done
    } > "$FILELIST"

    _transfer_count=$(wc -l < "$FILELIST")
    info "文件列表已生成: $_transfer_count 个文件，开始传输..."

    tar -czf - -T "$FILELIST" | \
        ssh "$REMOTE" "cd $REMOTE_DIR && tar --transform='s|^\./live/||' --transform='s|^\./asset_code/||' -xzf -"
    rm -f "$FILELIST"
fi

# ── 6. 验证 ──────────────────────────────────────────────
info "验证远程数据..."
remote_csv_count=$(ssh "$REMOTE" "cd $REMOTE_DIR && { find . -maxdepth 1 -name '*.csv' -type f; find ./live -maxdepth 1 -name '*.csv' -type f 2>/dev/null; find ./live_index -name '*.csv' -type f; find ./market_condition_live -name '*.csv' -type f; find ./asset_code -name '*.csv' -type f 2>/dev/null; for d in ./trade_point_live_inference_*/; do [ -d \"\$d\" ] && find \"\$d\" -name '*.csv' -type f; done; } 2>/dev/null | wc -l")
info "远程数据: $remote_csv_count 个 CSV 文件"

# ── 7. 完成 ──────────────────────────────────────────────
echo ""
echo -e "${CYAN}========================================="
echo " ✅ 数据同步完成！"
echo -e "=========================================${NC}"
echo ""
echo -e "  ${GREEN}$csv_count${NC} 个本地文件 → ${GREEN}$remote_csv_count${NC} 个远程文件"
echo ""
