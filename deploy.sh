#!/usr/bin/env bash
# ============================================================
# Quant-UI 一键部署脚本 (在 Linux 服务器上运行)
# ============================================================
# 用法:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# 可选环境变量:
#   DATA_DIR       数据文件目录 (默认 /home/ubuntu/quant-ui-data)
#   PORT           前端端口 (默认 3000)
#   LOG_LEVEL      日志级别 (默认 INFO)
# ============================================================
set -euo pipefail

# ── 颜色输出 ──────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

echo ""
echo -e "${CYAN}========================================="
echo " Quant-UI 一键部署"
echo -e "=========================================${NC}"
echo ""

# ── 1. 检查依赖 ──────────────────────────────────────────
info "检查系统依赖..."

command -v docker >/dev/null 2>&1 || {
    error "未安装 Docker，请先安装: curl -fsSL https://get.docker.com | sh"
}

# 检查 Docker 权限
if ! docker ps >/dev/null 2>&1; then
    error "Docker 权限不足，请执行以下命令后重新登录:\n  sudo usermod -aG docker \$USER && newgrp docker\n  或者用 sudo 运行本脚本: sudo ./deploy.sh"
fi

if docker compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
else
    error "未安装 Docker Compose，请先安装"
fi

info "Docker: $(docker --version)"
info "Compose: $($DOCKER_COMPOSE version --short 2>/dev/null || echo 'ok')"

# ── 2. 配置 ──────────────────────────────────────────────
DATA_DIR=${DATA_DIR:-/home/ubuntu/quant-ui-data}
PORT=${PORT:-3000}
LOG_LEVEL=${LOG_LEVEL:-INFO}

# 自动检测服务器 IP
SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="127.0.0.1"
fi

echo ""
info "配置信息:"
echo "   数据目录:   $DATA_DIR"
echo "   前端端口:   $PORT"
echo "   服务器 IP:  $SERVER_IP"
echo "   日志级别:   $LOG_LEVEL"
echo ""

# 允许用户修改配置
read -rp "是否需要修改以上配置? [y/N]: " change_config
if [ "$change_config" = "y" ] || [ "$change_config" = "Y" ]; then
    read -rp "数据目录 [$DATA_DIR]: " input
    DATA_DIR=${input:-$DATA_DIR}
    read -rp "前端端口 [$PORT]: " input
    PORT=${input:-$PORT}
fi

# ── 3. 创建数据目录结构 ──────────────────────────────────
info "创建数据目录..."

mkdir -p "$DATA_DIR"/{live,live_index,market_condition_live,output}
# 为每个策略创建信号目录（根据实际策略调整）
# 默认创建 fuzzy_ma 和 tea_radical_nature 两个策略目录
mkdir -p "$DATA_DIR"/trade_point_live_inference_fuzzy_ma
mkdir -p "$DATA_DIR"/trade_point_live_inference_tea_radical_nature

info "数据目录已创建: $DATA_DIR"

# ── 4. 生成 Docker 专用配置文件 ──────────────────────────
info "生成 config.docker.yaml..."

cat > config.docker.yaml << EOF
# Quant-UI Docker 配置文件 (自动生成于 $(date '+%Y-%m-%d %H:%M:%S'))
signal_root_dir: /data
price_root_dir: /data
output_dir: /data/output

# 指数行情文件路径
index_price_csv_path: /data/live_index/live_bar_A_000001_d.csv
index_condition_csv_path: /data/market_condition_live/A_000001_d.csv

# 股票名称映射文件 (可选)
stock_name_csv_path: /data/a800_stocks.csv

# 要加载的策略列表
default_strategy_list:
  - fuzzy_ma
  - tea_radical_nature

# 市场和级别默认值
default_market: A
default_level: d

# 交易成本
commission: 0.001
slippage: 0.001

# 指标参数
ma_periods:
  - 5
  - 10
  - 20
macd_fast: 12
macd_slow: 26
macd_signal: 9
atr_period: 14

# Web 服务 (Docker 内必须绑定 0.0.0.0)
app_host: "0.0.0.0"
app_port: 8765

# 日志
log_level: INFO
log_file: /data/output/app.log
EOF

info "配置文件已生成: config.docker.yaml"

# ── 5. 构建镜像 ──────────────────────────────────────────
info "构建 Docker 镜像..."
$DOCKER_COMPOSE build --no-cache

# ── 6. 启动服务 ──────────────────────────────────────────
info "启动服务..."
DATA_DIR=$DATA_DIR PORT=$PORT LOG_LEVEL=$LOG_LEVEL $DOCKER_COMPOSE up -d

# ── 7. 等待服务就绪 ──────────────────────────────────────
info "等待服务就绪..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8765/api/health >/dev/null 2>&1; then
        info "后端 API 已就绪"
        break
    fi
    if [ $i -eq 30 ]; then
        warn "后端启动超时，请检查日志: $DOCKER_COMPOSE logs backend"
    fi
    sleep 2
done

for i in $(seq 1 15); do
    if curl -s http://localhost:$PORT >/dev/null 2>&1; then
        info "前端页面已就绪"
        break
    fi
    if [ $i -eq 15 ]; then
        warn "前端启动超时，请检查日志: $DOCKER_COMPOSE logs frontend"
    fi
    sleep 2
done

# ── 8. 完成 ──────────────────────────────────────────────
echo ""
echo -e "${CYAN}========================================="
echo " 🚀 部署完成！"
echo -e "=========================================${NC}"
echo ""
echo -e "  访问地址:   ${GREEN}http://$SERVER_IP:$PORT${NC}"
echo -e "  API 地址:   ${GREEN}http://$SERVER_IP:8765${NC}"
echo -e "  数据目录:   ${GREEN}$DATA_DIR${NC}"
echo ""
echo -e "${YELLOW}下一步:${NC}"
echo -e "  1. 将 CSV 数据文件放入: ${CYAN}$DATA_DIR${NC}"
echo -e "  2. 或使用本地 ${CYAN}sync-data.sh${NC} 脚本同步数据"
echo ""
echo -e "${YELLOW}常用命令:${NC}"
echo "  $DOCKER_COMPOSE logs -f          查看日志"
echo "  $DOCKER_COMPOSE restart          重启服务"
echo "  $DOCKER_COMPOSE down             停止服务"
echo "  $DOCKER_COMPOSE up -d            启动服务"
echo ""
