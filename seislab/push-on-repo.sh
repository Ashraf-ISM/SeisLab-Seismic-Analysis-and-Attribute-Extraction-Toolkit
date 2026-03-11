#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║           GIT AUTOPUSH — PROFESSIONAL DEPLOY TOOL           ║
# ╚══════════════════════════════════════════════════════════════╝

RESET='\033[0m'; BOLD='\033[1m'; DIM='\033[2m'
RED='\033[31m'; GREEN='\033[32m'; YELLOW='\033[33m'
BLUE='\033[34m'; MAGENTA='\033[35m'; CYAN='\033[36m'; WHITE='\033[37m'
BG_BLACK='\033[40m'
BRIGHT_RED='\033[91m'; BRIGHT_GREEN='\033[92m'; BRIGHT_YELLOW='\033[93m'
BRIGHT_BLUE='\033[94m'; BRIGHT_MAGENTA='\033[95m'; BRIGHT_CYAN='\033[96m'; BRIGHT_WHITE='\033[97m'

spinner() {
    local pid=$1 msg="${2:-Processing...}"
    local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local colors=("$BRIGHT_CYAN" "$BRIGHT_BLUE" "$BRIGHT_MAGENTA" "$BRIGHT_CYAN" "$BRIGHT_BLUE")
    local i=0
    tput civis 2>/dev/null
    while kill -0 "$pid" 2>/dev/null; do
        local color=${colors[$((i % ${#colors[@]}))]}
        printf "\r  ${color}${frames[$((i % 10))]}${RESET}  ${DIM}${msg}${RESET}   "
        i=$((i + 1)); sleep 0.08
    done
    tput cnorm 2>/dev/null
    printf "\r%-60s\r" " "
}

progress_bar() {
    local duration=${1:-1} label="${2:-}" width=40
    local bar_char="█" empty_char="░"
    local colors=("$BRIGHT_BLUE" "$BRIGHT_CYAN" "$BRIGHT_MAGENTA" "$BRIGHT_GREEN")
    tput civis 2>/dev/null
    for ((i=0; i<=width; i++)); do
        local pct=$(( i * 100 / width ))
        local color=${colors[$((i * ${#colors[@]} / (width + 1)))]}
        local filled="" empty=""
        for ((f=0; f<i; f++)); do filled="${filled}${bar_char}"; done
        for ((e=0; e<(width-i); e++)); do empty="${empty}${empty_char}"; done
        printf "\r  ${DIM}[${RESET}${color}${filled}${RESET}${DIM}${empty}]${RESET} ${BRIGHT_WHITE}${pct}%%${RESET}  ${DIM}${label}${RESET}"
        sleep 0.025
    done
    tput cnorm 2>/dev/null; echo ""
}

section()     { echo ""; echo -e "  ${2:-$BRIGHT_CYAN}${BOLD}▸ $1${RESET}"; echo -e "  ${DIM}──────────────────────────────────────────────────${RESET}"; }
status_ok()   { echo -e "  ${BRIGHT_GREEN}✔${RESET}  ${WHITE}$1${RESET}"; }
status_warn() { echo -e "  ${BRIGHT_YELLOW}⚠${RESET}  ${YELLOW}$1${RESET}"; }
status_err()  { echo -e "  ${BRIGHT_RED}✘${RESET}  ${RED}$1${RESET}"; }
status_info() { echo -e "  ${BRIGHT_BLUE}ℹ${RESET}  ${DIM}$1${RESET}"; }
status_run()  { echo -e "  ${BRIGHT_MAGENTA}⟶${RESET}  ${WHITE}$1${RESET}"; }

clear; sleep 0.1; echo ""
echo -e "${BRIGHT_BLUE}${BOLD}"
echo "   ██████╗ ██╗████████╗    ██████╗ ██╗   ██╗███████╗██╗  ██╗"
echo "  ██╔════╝ ██║╚══██╔══╝    ██╔══██╗██║   ██║██╔════╝██║  ██║"
echo "  ██║  ███╗██║   ██║       ██████╔╝██║   ██║███████╗███████║"
echo "  ██║   ██║██║   ██║       ██╔═══╝ ██║   ██║╚════██║██╔══██║"
echo "  ╚██████╔╝██║   ██║       ██║     ╚██████╔╝███████║██║  ██║"
echo "   ╚═════╝ ╚═╝   ╚═╝       ╚═╝      ╚═════╝ ╚══════╝╚═╝  ╚═╝"
echo -e "${RESET}"
echo -e "  ${DIM}${CYAN}······························································${RESET}"
echo -e "  ${BRIGHT_MAGENTA}${BOLD}  Automated Commit & Deploy Engine${RESET}  ${DIM}v2.0 · Professional Edition${RESET}"
echo -e "  ${DIM}${CYAN}······························································${RESET}"
echo ""; sleep 0.3

section "ENVIRONMENT CHECK" "$BRIGHT_YELLOW"
sleep 0.1
if ! command -v git &>/dev/null; then status_err "Git not found."; exit 1; fi
status_ok "Git binary detected  $(git --version)"
sleep 0.1
if ! git rev-parse --git-dir &>/dev/null; then status_err "Not inside a Git repository."; exit 1; fi
status_ok "Repository verified"
sleep 0.1

BRANCH=$(git branch --show-current)
REMOTE=$(git remote get-url origin 2>/dev/null || echo "No remote configured")
LAST_COMMIT=$(git log -1 --pretty=format:"%h · %s" 2>/dev/null || echo "No commits yet")
status_info "Branch   : ${BRIGHT_WHITE}${BRANCH}${RESET}"
status_info "Remote   : ${BRIGHT_WHITE}${REMOTE}${RESET}"
status_info "Last     : ${BRIGHT_WHITE}${LAST_COMMIT}${RESET}"

section "WORKING TREE STATUS" "$BRIGHT_CYAN"; sleep 0.1
STATUS_OUTPUT=$(git status --short)
if [[ -z "$STATUS_OUTPUT" ]]; then
    status_warn "Working tree is clean — nothing to commit."
    echo -e "\n  ${DIM}Nothing to push. Exiting gracefully.${RESET}\n"; exit 0
fi
echo ""
while IFS= read -r line; do
    flag="${line:0:2}"; file="${line:3}"
    case "$flag" in
        "M "|" M") echo -e "  ${BRIGHT_YELLOW}  ≈  ${RESET}${YELLOW}modified  ${RESET}${WHITE}$file${RESET}" ;;
        "A "|" A") echo -e "  ${BRIGHT_GREEN}  +  ${RESET}${GREEN}added     ${RESET}${WHITE}$file${RESET}" ;;
        "D "|" D") echo -e "  ${BRIGHT_RED}  −  ${RESET}${RED}deleted   ${RESET}${WHITE}$file${RESET}" ;;
        "??")      echo -e "  ${BRIGHT_BLUE}  ?  ${RESET}${BLUE}untracked ${RESET}${DIM}$file${RESET}" ;;
        "R "|" R") echo -e "  ${BRIGHT_MAGENTA}  →  ${RESET}${MAGENTA}renamed   ${RESET}${WHITE}$file${RESET}" ;;
        *)         echo -e "  ${DIM}  ·  $line${RESET}" ;;
    esac
done <<< "$STATUS_OUTPUT"
echo ""
CHANGED_COUNT=$(echo "$STATUS_OUTPUT" | wc -l | tr -d ' ')
status_info "${CHANGED_COUNT} file(s) detected"

section "COMMIT MESSAGE" "$BRIGHT_MAGENTA"; echo ""
echo -e "  ${DIM}Write a clear, imperative-style message (e.g. \"Add login feature\")${RESET}\n"
printf "  ${BRIGHT_MAGENTA}${BOLD}❯${RESET} ${WHITE}"; read -r commit_message; printf "${RESET}"
if [[ -z "$commit_message" ]]; then echo ""; status_err "Commit message cannot be empty."; exit 1; fi
echo -e "\n  ${DIM}Message preview:${RESET}"
echo -e "  ${BG_BLACK}${BRIGHT_WHITE}  \" ${commit_message} \"  ${RESET}"

section "CONFIRM PUSH" "$BRIGHT_GREEN"; echo ""
echo -e "  ${DIM}Pushing to:${RESET}   ${BRIGHT_WHITE}${BOLD}origin/${BRANCH}${RESET}"
echo -e "  ${DIM}Message:${RESET}      ${BRIGHT_CYAN}${BOLD}\"${commit_message}\"${RESET}\n"
printf "  ${BRIGHT_GREEN}${BOLD}Proceed? ${RESET}${DIM}[y/N]${RESET} ${BRIGHT_WHITE}"; read -r confirm; printf "${RESET}"
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo ""; status_warn "Commit cancelled by user."
    echo -e "  ${DIM}No changes were made.${RESET}\n"; exit 0
fi

section "EXECUTING PIPELINE" "$BRIGHT_YELLOW"; echo ""

status_run "Staging all changes..."
(git add . > /tmp/gitpush_out 2>&1) &
spinner $! "Running git add ."
progress_bar 0.4 "Staging files"
status_ok "All files staged"; sleep 0.2

status_run "Creating commit..."
(git commit -m "$commit_message" > /tmp/gitpush_out 2>&1) &
CPID=$!; spinner $CPID "Running git commit"; wait $CPID; COMMIT_EXIT=$?
if [[ $COMMIT_EXIT -ne 0 ]]; then status_err "git commit failed."; cat /tmp/gitpush_out; exit 1; fi
progress_bar 0.5 "Writing commit object"
status_ok "Commit created"; sleep 0.2

status_run "Pushing to remote..."
(git push -u origin "$BRANCH" > /tmp/gitpush_out 2>&1) &
PUSH_PID=$!; spinner $PUSH_PID "Pushing to origin/${BRANCH}"; wait $PUSH_PID; PUSH_EXIT=$?
if [[ $PUSH_EXIT -ne 0 ]]; then
    echo ""; status_err "Push failed. Remote output:"
    while IFS= read -r line; do echo -e "  ${DIM}${RED}$line${RESET}"; done < /tmp/gitpush_out
    echo ""; exit 1
fi
progress_bar 0.7 "Uploading to remote"
status_ok "Push successful"

echo ""; sleep 0.2; echo ""
echo -e "  ${BRIGHT_GREEN}${BOLD}╔════════════════════════════════════════════════════════════╗${RESET}"
echo -e "  ${BRIGHT_GREEN}${BOLD}║${RESET}${BRIGHT_WHITE}${BOLD}            ✦  DEPLOY COMPLETE — SHIP IT!  ✦              ${BRIGHT_GREEN}${BOLD}║${RESET}"
echo -e "  ${BRIGHT_GREEN}${BOLD}╚════════════════════════════════════════════════════════════╝${RESET}"
echo ""

NEW_HASH=$(git log -1 --pretty=format:"%h")
NEW_TIME=$(git log -1 --pretty=format:"%cr")
echo -e "  ${DIM}──────────────────────────────────────────────────${RESET}"
echo -e "  ${BRIGHT_GREEN}✔${RESET}  ${WHITE}Branch   ${RESET}${BRIGHT_CYAN}${BOLD}${BRANCH}${RESET}"
echo -e "  ${BRIGHT_GREEN}✔${RESET}  ${WHITE}Commit   ${RESET}${BRIGHT_YELLOW}${BOLD}${NEW_HASH}${RESET}"
echo -e "  ${BRIGHT_GREEN}✔${RESET}  ${WHITE}Message  ${RESET}${DIM}\"${commit_message}\"${RESET}"
echo -e "  ${BRIGHT_GREEN}✔${RESET}  ${WHITE}Pushed   ${RESET}${DIM}${NEW_TIME}${RESET}"
echo -e "  ${BRIGHT_GREEN}✔${RESET}  ${WHITE}Files    ${RESET}${DIM}${CHANGED_COUNT} changed${RESET}"
echo ""
echo -e "  ${DIM}${CYAN}······························································${RESET}"
echo -e "  ${DIM}  Have a great day. Happy shipping!  �${RESET}"
echo -e "  ${DIM}${CYAN}······························································${RESET}"
echo ""
rm -f /tmp/gitpush_out; exit 0