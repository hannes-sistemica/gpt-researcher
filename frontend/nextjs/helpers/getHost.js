export const getHost = ({ purpose } = {}) => {
  if (typeof window !== 'undefined') {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    let protocol, host;

    if (backendUrl) {
      try {
        const url = new URL(backendUrl);
        protocol = url.protocol.slice(0, -1); // Remove the trailing colon
        host = url.host;
      } catch (error) {
        console.error('Invalid NEXT_PUBLIC_BACKEND_URL:', backendUrl);
        // Fallback to default behavior if URL is invalid
        protocol = window.location.protocol.slice(0, -1);
        host = window.location.host;
      }
    } else {
      // Fallback to original logic if environment variable is not set
      protocol = window.location.protocol.slice(0, -1);
      host = window.location.host;
      if (host.includes('localhost')) {
        return purpose === 'langgraph-gui'
          ? 'http%3A%2F%2F127.0.0.1%3A8123'
          : 'http://localhost:8000';
      }
    }

    // Handle the special case for langgraph-gui
    if (purpose === 'langgraph-gui') {
      return `${protocol}%3A%2F%2F${host}`;
    }

    return `${protocol}://${host}`;
  }
  return '';
};