import Modal from './Modal'

export default function ConfirmDialog({ open, onClose, onConfirm, title, message, confirmLabel = 'Elimina', danger = true, loading = false }) {
  return (
    <Modal open={open} onClose={onClose} title={title}>
      <p className="text-sm text-gray-600">{message}</p>
      <div className="flex gap-2 mt-4 justify-end">
        <button className="btn-secondary" onClick={onClose}>Annulla</button>
        <button
          className={danger ? 'btn-danger' : 'btn-primary'}
          onClick={onConfirm}
          disabled={loading}
        >
          {loading ? 'Attendere...' : confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
