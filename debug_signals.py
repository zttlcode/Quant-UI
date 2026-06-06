"""Diagnostic script: call loader internals directly to find the bug."""
import sys, logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Enable DEBUG logging to see all internal messages
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] %(name)s | %(message)s",
)

from src.config.settings import get_config
from src.data_loader.signal_loader import SignalLoader

config = get_config()
loader = SignalLoader(config)

# Bypass load_strategy_signals — call internals manually
dir_path = Path(config.signal_root_dir) / "trade_point_live_inference_fuzzy_ma"
print(f"\nDirect internal test:")
print(f"  dir_path = {dir_path}")

from src.utils.file_utils import scan_csv_files, parse_filename
csv_files = scan_csv_files(str(dir_path), "*.csv")

for fp in csv_files:
    print(f"\n{'='*50}")
    print(f"Processing: {fp.name}")

    # Step A: parse filename
    parsed = parse_filename(fp.name, pattern_type="signal")
    market, stock_code, level = parsed["market"], parsed["code"], parsed["level"]
    print(f"  Parsed: market={market}, code={stock_code}, level={level}")

    # Step B: read CSV
    try:
        df = loader._read_signal_csv(fp)
        print(f"  DataFrame: {len(df)} rows, columns={list(df.columns)}")
        print(f"  df.empty = {df.empty}")
        if not df.empty:
            print(f"  First row: {df.iloc[0].to_dict()}")
    except Exception as e:
        print(f"  ERROR reading CSV: {e}")
        import traceback
        traceback.print_exc()
        continue

    # Step C: parse signals
    try:
        signals = loader._parse_signals(df, stock_code, market, level, "fuzzy_ma")
        print(f"  Parsed signals: {len(signals)}")
        for s in signals:
            print(f"    -> {s.stock_code} {s.date_str} {s.signal.value} price={s.price} label={s.label} prob={s.prob}")
    except Exception as e:
        print(f"  ERROR parsing signals: {e}")
        import traceback
        traceback.print_exc()

# Step D: dedup
all_signals = []
for fp in csv_files:
    parsed = parse_filename(fp.name, pattern_type="signal")
    market, stock_code, level = parsed["market"], parsed["code"], parsed["level"]
    df = loader._read_signal_csv(fp)
    if not df.empty:
        s = loader._parse_signals(df, stock_code, market, level, "fuzzy_ma")
        all_signals.extend(s)

print(f"\n{'='*50}")
print(f"Before dedup: {len(all_signals)} signals")
for s in all_signals:
    print(f"  {s.stock_code}: {s.date_str} {s.signal.value}")

deduped = loader._deduplicate_signals(all_signals)
print(f"After dedup: {len(deduped)} signals")
for s in deduped:
    print(f"  {s.stock_code}: {s.date_str} {s.signal.value}")
