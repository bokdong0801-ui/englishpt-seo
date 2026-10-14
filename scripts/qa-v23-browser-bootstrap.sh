#!/usr/bin/env bash
# No QA is marked PASS unless the browser's debugging endpoint is truly ready.
V23_CHROME_PID=""
V23_SERVER_PID=""
V23_BROWSER_PROFILE=""
start_v23_review_browser() {
  local http_port="$1" debug_port="$2" serve_dir="$3" label="$4"
  local chrome=""
  chrome="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)"
  if [[ -z "$chrome" ]]; then echo "::error::Chrome executable missing"; return 1; fi
  local http_log="/tmp/$label-http.log" chrome_log="/tmp/$label-chrome.log"
  python3 -m http.server "$http_port" --bind 127.0.0.1 --directory "$serve_dir" >"$http_log" 2>&1 &
  V23_SERVER_PID=$!
  local i attempt ready
  for i in $(seq 1 50); do
    if curl --max-time 2 -fsS "http://127.0.0.1:$http_port/" >/dev/null 2>&1; then break; fi
    sleep .2
  done
  if ! curl --max-time 2 -fsS "http://127.0.0.1:$http_port/" >/dev/null 2>&1; then
    echo "::error::HTTP server port $http_port failed"
    tail -n 60 "$http_log" || true
    return 1
  fi
  for attempt in 1 2 3; do
    V23_BROWSER_PROFILE="$(mktemp -d "/tmp/$label-chrome-$attempt-XXXXXX")"
    echo "Chrome attempt $attempt/3: $chrome on port $debug_port"
    "$chrome" --headless=new --no-sandbox --disable-dev-shm-usage --disable-gpu \
      --disable-background-networking --disable-extensions --no-first-run \
      --no-default-browser-check --disable-default-apps --hide-scrollbars \
      --remote-debugging-address=127.0.0.1 --remote-debugging-port="$debug_port" \
      --remote-allow-origins='*' --user-data-dir="$V23_BROWSER_PROFILE" \
      about:blank >"$chrome_log" 2>&1 &
    V23_CHROME_PID=$!
    ready=0
    for i in $(seq 1 120); do
      if curl --max-time 2 -fsS "http://127.0.0.1:$debug_port/json/version" >/dev/null 2>&1; then
        ready=1; break
      fi
      if ! kill -0 "$V23_CHROME_PID" 2>/dev/null; then
        echo "Chrome exited before debugger became available"; break
      fi
      sleep .5
    done
    if [[ "$ready" == 1 ]]; then
      echo "PASS_V23_CHROME_READY attempt=$attempt port=$debug_port"
      return 0
    fi
    echo "::warning::Chrome attempt $attempt failed; startup details:"
    tail -n 90 "$chrome_log" || true
    ps -eo pid,ppid,stat,rss,comm | grep -E 'chrome|chromium' | tail -n 25 || true
    kill "$V23_CHROME_PID" 2>/dev/null || true
    rm -rf "$V23_BROWSER_PROFILE" >/dev/null 2>&1 || true
    sleep 1
  done
  echo "::error::Chromium debugging endpoint $debug_port failed after 3 attempts"
  df -h /tmp . || true
  free -m || true
  return 1
}
stop_v23_review_browser() {
  if [[ -n "$V23_CHROME_PID" ]]; then kill "$V23_CHROME_PID" 2>/dev/null || true; fi
  if [[ -n "$V23_SERVER_PID" ]]; then kill "$V23_SERVER_PID" 2>/dev/null || true; fi
  if [[ -n "$V23_BROWSER_PROFILE" && -d "$V23_BROWSER_PROFILE" ]]; then rm -rf "$V23_BROWSER_PROFILE" >/dev/null 2>&1 || true; fi
  V23_CHROME_PID=""
  V23_SERVER_PID=""
  V23_BROWSER_PROFILE=""
}
