# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

from ui_database.matcher import match_screenshot
from ui_database.settings import DEFAULT_GAME


def main():
    parser = argparse.ArgumentParser(description="Match a screenshot against the local UI database.")
    parser.add_argument("image", type=Path, help="Screenshot image path")
    parser.add_argument("--game", default=DEFAULT_GAME, help="Game name to search first")
    args = parser.parse_args()

    print("=" * 48)
    print("UI Screenshot Matcher")
    print(f"Image: {args.image}")

    result = match_screenshot(args.image, game=args.game)
    if not result.get("matched"):
        print("No reliable match found.")
        print(f"Best template: {result.get('template_id', 'none')}")
        print(f"Score: {result.get('score', 0):.3f}")
        print(f"Reason: {result.get('reason', 'unknown')}")
        print("Fallback: original AI vision")
        print("=" * 48)
        return 1

    print(f"Best Match: {result['template_id']} · {result['template_name']}")
    print(f"Score: {result['score']:.3f}")
    print(f"Resolution: {result['screen_size'][0]}x{result['screen_size'][1]}")
    print(f"UI Elements: {result['ui_count']}")
    for index, element in enumerate(result["ui_elements"], start=1):
        print(f"{index}. {element['name']} — {element['function']}")
        print(f"   center = ({element['center_x']}, {element['center_y']})")
        print(f"   bbox = {element['bbox']}")
    print("=" * 48)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
