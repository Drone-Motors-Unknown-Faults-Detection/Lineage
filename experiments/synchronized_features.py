"""Raw→shared windows→new105 CSV/sidecar, without copying raw or changing formal data."""
import argparse
import json
from pathlib import Path
from core.synchronized_features import generate, VARIANTS
from core.logger import setup_run


def run(pools, *, settings, output, incoming_root):
    return generate(pools,settings=settings,output=output,incoming_root=incoming_root)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw-file",type=Path,required=True); p.add_argument("--config",type=Path,required=True)
    p.add_argument("--incoming-root",type=Path,required=True)
    p.add_argument("--variant",choices=VARIANTS,required=True)
    args=p.parse_args(); log,paths=setup_run("synchronized_features")
    cfg=json.loads(args.config.read_text(encoding="utf-8"))
    result=run([(args.raw_file,cfg)],settings={"variant":args.variant,"quality":cfg["quality"],"windows":cfg["windows"]},output=paths.output_dir,incoming_root=args.incoming_root)
    log.info("rows={} version={} (not model validation)",result["rows"],result["registry"]["feature_version"])


if __name__ == "__main__": main()
