import React from 'react';
import Modal from '../common/Modal';
import DeviceForm from './DeviceForm';

type DeviceModalProps = {
  isOpen: boolean;
  onClose: () => void;
  initial?: { name: string; status: string };
  onSave: (data: { name: string; status: string }) => void;
  loading?: boolean;
};

const DeviceModal: React.FC<DeviceModalProps> = ({ isOpen, onClose, initial, onSave, loading }) => (
  <Modal isOpen={isOpen} onClose={onClose} title={initial ? 'Edit Device' : 'Add Device'}>
    <DeviceForm initial={initial} onSubmit={onSave} loading={loading} />
  </Modal>
);

export default DeviceModal;
