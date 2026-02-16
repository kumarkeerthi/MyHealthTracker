export function ProfileView({ chapatiCount, chapatiLimit, recipeSuggestion }: { chapatiCount: number; chapatiLimit: number; recipeSuggestion: string }) {
  return (
    <section className="space-y-3">
      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Profile</p>
        <p className="mt-2 text-sm text-slate-200">Chapati cap: {chapatiCount}/{chapatiLimit}</p>
      </div>
      <div className="glass-card p-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-400">Smart Suggestion</p>
        <p className="mt-2 text-sm text-slate-300">{recipeSuggestion}</p>
      </div>
    </section>
  );
}
