import type { ReactNode } from "react";

const NUMERIC_SEGMENT_PATTERN = /([+-]?\$?\d[\d,]*(?:\.\d+)?%?)/g;

export function emphasizeNumericText(text: string): ReactNode {
  if (text === "" || !/\d/.test(text)) {
    return text;
  }

  const parts: ReactNode[] = [];
  let cursor = 0;
  for (const match of text.matchAll(NUMERIC_SEGMENT_PATTERN)) {
    const matchedValue = match[0];
    const start = match.index ?? -1;
    if (start < 0) {
      continue;
    }
    const end = start + matchedValue.length;
    if (start > cursor) {
      parts.push(text.slice(cursor, start));
    }
    parts.push(
      <strong key={`numeric-segment-${start}-${end}`}>{matchedValue}</strong>
    );
    cursor = end;
  }

  if (parts.length === 0) {
    return text;
  }
  if (cursor < text.length) {
    parts.push(text.slice(cursor));
  }
  return <>{parts}</>;
}
