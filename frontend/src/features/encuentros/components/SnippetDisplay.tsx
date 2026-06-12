import { useState, type ReactNode } from 'react';

interface SnippetDisplayProps {
  snippet: string;
}

function SnippetDisplay({ snippet }: SnippetDisplayProps): ReactNode {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(snippet);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: select text
      const textarea = document.querySelector('#snippet-textarea') as HTMLTextAreaElement;
      if (textarea) {
        textarea.select();
        document.execCommand('copy');
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    }
  };

  return (
    <div className="space-y-3">
      <textarea
        id="snippet-textarea"
        readOnly
        value={snippet}
        rows={6}
        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono bg-gray-50"
      />
      <button
        type="button"
        onClick={handleCopy}
        className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
          copied
            ? 'bg-green-600 text-white'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {copied ? 'Copiado!' : 'Copiar al portapapeles'}
      </button>
    </div>
  );
}

export default SnippetDisplay;
