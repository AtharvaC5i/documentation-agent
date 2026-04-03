import { useEffect, useRef, useCallback } from "react";

export function usePolling(fn, interval = 2000, active = true) {
  const timer = useRef(null);
  const savedFn = useRef(fn);

  useEffect(() => { savedFn.current = fn; }, [fn]);

  const stop = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
  }, []);

  useEffect(() => {
    if (!active) { stop(); return; }
    savedFn.current();
    timer.current = setInterval(() => savedFn.current(), interval);
    return stop;
  }, [active, interval, stop]);

  return { stop };
}
