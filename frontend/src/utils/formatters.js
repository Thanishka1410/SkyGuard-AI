export function formatTimeString(ts) {
  if (!ts) return '';
  const str = String(ts).replace(' ', 'T');
  const d = new Date(str);
  if (!isNaN(d.getTime())) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  if (String(ts).length >= 8) {
    return String(ts).slice(-8);
  }
  return String(ts);
}
