import { useState, useEffect } from "react";
import { checkHealth } from "../api/endpoints";

export function useApiStatus() {
  const [online, setOnline] = useState(false);

  useEffect(() => {
    let mounted = true;

    const check = async () => {
      try {
        await checkHealth();
        if (mounted) setOnline(true);
      } catch {
        if (mounted) setOnline(false);
      }
    };

    check();
    const interval = setInterval(check, 10_000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return online;
}
