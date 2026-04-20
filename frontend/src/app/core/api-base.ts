function isLocalDevHost(hostname: string) {
  return hostname === 'localhost' || hostname === '127.0.0.1';
}

export function resolveApiBaseUrl() {
  if (typeof window === 'undefined') {
    return 'http://127.0.0.1:8000/api';
  }

  const { protocol, hostname, port, origin } = window.location;

  if (isLocalDevHost(hostname) && (port === '4200' || port === '3000' || port === '5173')) {
    return 'http://127.0.0.1:8000/api';
  }

  if (isLocalDevHost(hostname) && port === '8000') {
    return `${protocol}//${hostname}:8000/api`;
  }

  return `${origin}/api`;
}
