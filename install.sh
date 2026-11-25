#!/usr/bin/env bash
# task-report-kit 스킬을 Codex와 Claude Code 사용자 폴더에 설치한다.
#
# 사용법 (저장소 폴더에서 실행):
#   ./install.sh            Codex와 Claude Code 모두 복사 설치
#   ./install.sh --link     복사 대신 심볼릭 링크 (저장소를 git pull로 업데이트할 때)
#   ./install.sh --codex    Codex만
#   ./install.sh --claude   Claude Code만
#
# 이미 설치된 폴더는 덮어쓰지 않는다. 업데이트할 때는 기존 폴더를 확인하고 지운 뒤 다시 실행한다.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS=(task-asis-tobe task-asis task-tobe)
MODE=copy
TARGETS=()

for arg in "$@"; do
  case "$arg" in
    --link) MODE=link ;;
    --codex) TARGETS+=("$HOME/.agents/skills") ;;
    --claude) TARGETS+=("$HOME/.claude/skills") ;;
    -h|--help) sed -n 2,10p "$0"; exit 0 ;;
    *) echo "알 수 없는 옵션: $arg" >&2; exit 1 ;;
  esac
done
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=("$HOME/.agents/skills" "$HOME/.claude/skills")

for dir in "${TARGETS[@]}"; do
  mkdir -p "$dir"
  for s in "${SKILLS[@]}"; do
    dest="$dir/$s"
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      echo "건너뜀: $dest 가 이미 있습니다. 확인 후 지우고 다시 실행하세요."
      continue
    fi
    if [ "$MODE" = link ]; then
      ln -s "$ROOT/skills/$s" "$dest"
    else
      cp -R "$ROOT/skills/$s" "$dest"
    fi
    echo "설치: $dest"
  done
  if [ ! -e "$dir/natural-writing-kr" ]; then
    echo "참고: $dir 에 natural-writing-kr 가 없습니다. 함께 쓰려면 https://github.com/slobbie/natural-writing-kr 를 설치하세요."
  fi
done

echo "완료. 새 세션을 열면 Claude Code는 /task-asis, /task-asis-tobe, /task-tobe, Codex는 \$task-asis, \$task-asis-tobe, \$task-tobe 로 부를 수 있습니다."
