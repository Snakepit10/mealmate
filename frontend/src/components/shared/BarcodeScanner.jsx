import { useEffect, useRef, useState } from 'react'
import { X, SwitchCamera } from 'lucide-react'

export default function BarcodeScanner({ onResult, onClose }) {
  const videoRef = useRef(null)
  const [error, setError] = useState('')
  const [scanning, setScanning] = useState(true)
  const [devices, setDevices] = useState([])
  const [deviceId, setDeviceId] = useState(null) // null = auto (back camera)

  useEffect(() => {
    let codeReader
    let cancelled = false

    async function start() {
      try {
        const { BrowserMultiFormatReader } = await import('@zxing/library')
        codeReader = new BrowserMultiFormatReader()
        const allDevices = await codeReader.listVideoInputDevices()
        if (!cancelled) setDevices(allDevices)

        // Auto-select: usa la fotocamera posteriore (indice 1 se disponibile)
        const selectedId = deviceId ?? (allDevices.length > 1 ? allDevices[1].deviceId : allDevices[0]?.deviceId)

        await codeReader.decodeFromVideoDevice(selectedId, videoRef.current, (result) => {
          if (cancelled) return
          if (result) {
            setScanning(false)
            onResult(result.getText())
          }
        })
      } catch {
        if (!cancelled) setError('Impossibile accedere alla fotocamera')
      }
    }

    start()
    return () => {
      cancelled = true
      codeReader?.reset()
    }
  }, [deviceId, onResult])

  function switchCamera() {
    if (devices.length <= 1) return
    const currentIdx = deviceId
      ? devices.findIndex(d => d.deviceId === deviceId)
      : devices.length > 1 ? 1 : 0
    const nextIdx = (currentIdx + 1) % devices.length
    setDeviceId(devices[nextIdx].deviceId)
    setScanning(true)
    setError('')
  }

  // Etichetta fotocamera corrente (se disponibile)
  const currentDevice = deviceId
    ? devices.find(d => d.deviceId === deviceId)
    : devices[devices.length > 1 ? 1 : 0]
  const cameraLabel = currentDevice?.label
    ? currentDevice.label.replace(/\s*\(.*?\)\s*/g, '').trim()
    : devices.length > 1 ? `Fotocamera ${devices.indexOf(currentDevice) + 1}` : ''

  return (
    <div className="fixed inset-0 z-50 bg-black flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 text-white">
        <span className="font-medium">Scansiona barcode</span>
        <div className="flex items-center gap-1">
          {devices.length > 1 && (
            <button
              onClick={switchCamera}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
              title="Cambia fotocamera"
            >
              <SwitchCamera size={20} />
            </button>
          )}
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>
      </div>

      <div className="flex-1 relative">
        <video ref={videoRef} className="w-full h-full object-cover" />
        {/* Cornice di mira */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-64 h-40 border-2 border-white rounded-lg opacity-80" />
        </div>
      </div>

      {/* Nome fotocamera attiva */}
      {cameraLabel && devices.length > 1 && !error && (
        <div className="px-4 py-2 bg-black/70 text-white/70 text-xs text-center">
          {cameraLabel}
        </div>
      )}

      {error && (
        <div className="px-4 py-3 bg-red-900 text-red-100 text-sm text-center">
          {error}
        </div>
      )}

      {!scanning && (
        <div className="px-4 py-3 bg-primary-700 text-white text-sm text-center">
          Barcode rilevato!
        </div>
      )}
    </div>
  )
}
