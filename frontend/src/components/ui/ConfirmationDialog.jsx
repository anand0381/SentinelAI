import Button from './Button.jsx';
import Modal from './Modal.jsx';

function ConfirmationDialog({
  confirmLabel = 'Confirm',
  description,
  onCancel,
  onConfirm,
  open,
  title,
}) {
  return (
    <Modal open={open} title={title}>
      <p className="text-sm leading-6 text-slate-300">{description}</p>
      <div className="mt-6 flex justify-end gap-3">
        <Button onClick={onCancel} variant="secondary">
          Cancel
        </Button>
        <Button onClick={onConfirm} variant="danger">
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  );
}

export default ConfirmationDialog;
