// React
import { useCallback, useEffect, useRef, useState } from "react";

export interface FeedbackMessage {
  variant: "success" | "danger";
  text: string;
}

/**
 * Holds a feedback message (success or error) that clears itself after a timeout.
 * @param timeoutMs How long the message stays visible (defaults to 5000 ms)
 */
export function useFeedback(timeoutMs = 5000) {
  const [feedback, setFeedback] = useState<FeedbackMessage | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearFeedback = useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    setFeedback(null);
  }, []);

  const showFeedback = useCallback(
    (variant: FeedbackMessage["variant"], text: string) => {
      if (timer.current) clearTimeout(timer.current);
      setFeedback({ variant, text });
      timer.current = setTimeout(() => setFeedback(null), timeoutMs);
    },
    [timeoutMs],
  );

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );

  return { feedback, showFeedback, clearFeedback };
}
