import { useRef } from 'react'
import { Camera, X } from 'lucide-react'

/**
 * ImageUpload — click to select image, shows preview, optional remove button.
 * Props:
 *   preview: string|null  — existing image URL or local object URL
 *   onChange: (file: File|null) => void
 *   className: string
 *   aspectRatio: 'square'|'wide'  (default: 'wide')
 */
export default function ImageUpload({ preview, onChange, className = '', aspectRatio = 'wide' }) {
  const inputRef = useRef(null)

  function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    onChange(file)
    // Reset so the same file can be re-selected
    e.target.value = ''
  }

  function handleRemove(e) {
    e.stopPropagation()
    onChange(null)
  }

  const aspectClass = aspectRatio === 'square' ? 'aspect-square' : 'aspect-video'

  return (
    <div
      className={`relative ${aspectClass} rounded-xl overflow-hidden bg-gray-100 cursor-pointer group ${className}`}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFile}
      />

      {preview ? (
        <>
          <img src={preview} alt="Anteprima" className="w-full h-full object-cover" />
          <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <Camera size={24} className="text-white" />
          </div>
          <button
            type="button"
            onClick={handleRemove}
            className="absolute top-2 right-2 w-7 h-7 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center text-white transition-colors"
          >
            <X size={14} />
          </button>
        </>
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400 hover:text-gray-600 transition-colors">
          <Camera size={28} className="mb-1" />
          <p className="text-xs font-medium">Aggiungi foto</p>
        </div>
      )}
    </div>
  )
}
