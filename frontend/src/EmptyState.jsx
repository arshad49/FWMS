export default function EmptyState({ icon: Icon, title, description, actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 flex items-center justify-center mb-5">
        <Icon size={36} className="text-blue-900" />
      </div>
      <h3 className="text-lg font-bold text-slate-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 max-w-sm mb-6">{description}</p>
      {actionLabel && (
        <button 
          onClick={onAction}
          className="px-4 py-2 bg-blue-900 text-white rounded-lg hover:bg-blue-800 transition text-sm font-medium flex items-center gap-2"
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}