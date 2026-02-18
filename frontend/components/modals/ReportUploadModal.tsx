'use client';

import { useMemo, useState } from 'react';
import { AppModal } from '@/components/ui/AppModal';
import { confirmReport, type ParsedReport, uploadReport } from '@/lib/api';
import { useDashboardData } from '@/context/dashboard-data-context';
import { useToast } from '@/components/ui/toast';

const prettyBytes = (bytes: number) => `${(bytes / (1024 * 1024)).toFixed(2)} MB`;

export default function ReportUploadModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [loading, setLoading] = useState(false);
  const [parsed, setParsed] = useState<ParsedReport | null>(null);
  const { refreshDashboard } = useDashboardData();
  const { show } = useToast();

  const previewUrl = useMemo(() => (file && file.type.startsWith('image/') ? URL.createObjectURL(file) : null), [file]);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    try {
      setProgress(25);
      const res = await uploadReport(file);
      setProgress(80);
      setParsed(res);
      setProgress(100);
      show('success', 'Report parsed');
    } catch {
      show('error', 'Report parse failed');
    } finally {
      setLoading(false);
    }
  };

  const save = async () => {
    if (!parsed) return;
    setLoading(true);
    try {
      await confirmReport(parsed);
      show('success', 'Report saved');
      await refreshDashboard();
      onClose();
    } catch {
      show('error', 'Unable to save report');
    } finally {
      setLoading(false);
    }
  };

  const removeRow = (index: number) => {
    if (!parsed) return;
    setParsed({ ...parsed, parameters: parsed.parameters.filter((_, i) => i !== index) });
  };

  return (
    <AppModal open={open} onClose={onClose} title="Upload Report">
      <div className="space-y-3">
        <div className="rounded border border-dashed border-white/30 p-3">
          <input aria-label="Upload report file" type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
        {file ? <p className="text-xs text-slate-300">{file.name} • {prettyBytes(file.size)}</p> : null}
        {previewUrl ? <img src={previewUrl} alt="Report preview" className="max-h-40 rounded" /> : file ? <div className="rounded bg-white/10 p-2 text-sm">PDF selected</div> : null}
        <div className="h-2 w-full rounded bg-white/10"><div className="h-full rounded bg-cyan-500" style={{ width: `${progress}%` }} /></div>
        <div className="flex gap-2">
          <button className="rounded bg-cyan-600 px-3 py-2" onClick={() => void handleUpload()} disabled={loading || !file} type="button">{loading ? 'Parsing...' : 'Upload & Parse'}</button>
          <button className="rounded bg-emerald-600 px-3 py-2" onClick={() => void save()} disabled={loading || !parsed} type="button">Confirm Save</button>
        </div>
        {parsed ? (
          <div className="overflow-auto rounded border border-white/20">
            <table className="w-full text-sm">
              <thead><tr><th className="p-2 text-left">Parameter</th><th className="p-2">Value</th><th className="p-2">Unit</th><th className="p-2">Date</th><th className="p-2">Action</th></tr></thead>
              <tbody>
                {parsed.parameters.map((row, index) => (
                  <tr key={`${row.name}-${index}`} className="border-t border-white/10">
                    <td className="p-2">{row.name}</td>
                    <td className="p-2"><input value={row.value} onChange={(e) => setParsed((prev) => prev ? { ...prev, parameters: prev.parameters.map((p, i) => i === index ? { ...p, value: Number(e.target.value) } : p) } : prev)} className="w-20 rounded bg-white/10 p-1" /></td>
                    <td className="p-2">{row.unit}</td>
                    <td className="p-2">{parsed.report_date ?? '-'}</td>
                    <td className="p-2"><button className="text-rose-300" onClick={() => removeRow(index)} type="button">Remove</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </AppModal>
  );
}
