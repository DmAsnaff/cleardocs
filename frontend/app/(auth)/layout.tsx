export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">ClearDocs</h1>
          <p className="text-gray-500 mt-1 text-sm">Understand any document in plain English</p>
        </div>
        {children}
      </div>
    </div>
  );
}
