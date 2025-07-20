/**
 * Uploads a file to the backend and returns the extracted text.
 * @param file The file to upload.
 * @returns The JSON response from the API.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export const uploadFile = async (file: File, onProgress: (progress: number) => void): Promise<{ filename: string; message: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  // Since the backend is now synchronous, we don't have progress updates during upload.
  // We can simulate a bit of progress for UX.
  onProgress(50); // Simulate progress

  const response = await fetch(`${API_BASE_URL}/uploadfile/`, {
    method: 'POST',
    body: formData,
  });

  onProgress(100); // Mark as complete

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || 'File upload failed');
  }

  return response.json();
};

/**
 * Posts a query to the backend and returns the answer.
 * @param query The user's question.
 * @param filename The filename associated with the query.
 * @param history The conversation history.
 * @param textContent The text content of the file.
 * @returns The JSON response from the API containing the answer.
 */
export const postQuery = async (query: string, activeFiles: string[], chatHistory: Message[]): Promise<{ answer: string }> => {
  const response = await fetch(`${API_BASE_URL}/query/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
        body: JSON.stringify({
      query,
      filenames: activeFiles,
      chat_history: chatHistory.map(m => ({ role: m.role, content: m.content }))
    }),
  });

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  return response.json();
};
