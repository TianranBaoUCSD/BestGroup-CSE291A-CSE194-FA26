// Keeps asking the API until it has an answer, so a page opened before the API or
// its data is ready fills itself in without a refresh.

const FIRST_DELAY_MS = 1000;
const MAX_DELAY_MS = 30000;

/** 1s, 2s, 4s … up to 30s. */
export function retryDelay(attempt) {
  return Math.min(FIRST_DELAY_MS * 2 ** attempt, MAX_DELAY_MS);
}

/** Worth trying again: the server couldn't be reached or failed. A 4xx won't fix itself. */
export function isRetryable(err) {
  return err?.status === 0 || err?.status >= 500;
}

/**
 * Calls load() until it returns something `isReady` accepts, reporting every attempt.
 * Waits longer after each failure, and stops on an error that isn't retryable.
 * Returns a function that cancels any further attempts.
 */
export function loadWithRetry(load, { isReady, onResult, onError }) {
  let cancelled = false;
  let timer = null;
  let attempt = 0;

  const scheduleNext = () => {
    timer = setTimeout(run, retryDelay(attempt));
    attempt += 1;
  };

  function run() {
    load().then(
      (result) => {
        if (cancelled) return;
        onResult?.(result);
        if (!isReady(result)) scheduleNext();
      },
      (err) => {
        if (cancelled) return;
        onError?.(err);
        if (isRetryable(err)) scheduleNext();
      },
    );
  }

  run();
  return () => {
    cancelled = true;
    clearTimeout(timer);
  };
}
