import { useEffect, useRef, useCallback } from 'react'

function getWsBase() {
  const envBase = import.meta.env.VITE_WS_BASE
  if (envBase) return envBase
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}`
}

export function useWS(path, handlers) {
  const wsRef = useRef(null)
  const handlersRef = useRef(handlers)
  handlersRef.current = handlers

  const connect = useCallback(() => {
    if (!path) return
    const token = localStorage.getItem('access')
    if (!token) return

    const url = `${getWsBase()}${path}?token=${token}`
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      handlersRef.current?.onOpen?.()
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        handlersRef.current?.onMessage?.(msg)
        const handler = handlersRef.current?.[msg.type]
        if (handler) handler(msg)
      } catch {}
    }

    ws.onerror = () => {}

    ws.onclose = (event) => {
      handlersRef.current?.onClose?.(event)
      // Auto-reconnect after 3s unless intentionally closed
      if (event.code !== 1000) {
        setTimeout(connect, 3000)
      }
    }
  }, [path])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null // Prevent reconnect on unmount
        wsRef.current.close(1000)
      }
    }
  }, [connect])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
    }
  }, [])

  return { send }
}
