/**
 * Uploads a file to the backend and returns the extracted text.
 * @param file The file to upload.
 * @returns The JSON response from the API.
 */
const API_BASE_URL = 'http://127.0.0.1:8000';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface StatusResponse {
  status: 'processing' | 'completed' | 'failed' | 'not_found';
  text_content?: string;
  message?: string;
  progress?: number;
}

export const uploadFile = async (file: File): Promise<{ filename: string; message: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/uploadfile/`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
    throw new Error(errorData.detail || 'Failed to upload file.');
  }

  return response.json();
};

export const checkStatus = async (filename: string): Promise<StatusResponse> => {
  const response = await fetch(`${API_BASE_URL}/status/${filename}`);
  if (!response.ok) {
    throw new Error('Network response was not ok when checking status');
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
export const postQuery = async (query: string, filename: string, chatHistory: Message[], textContent: string): Promise<{ answer: string }> => {
  const response = await fetch(`${API_BASE_URL}/query/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      filename,
      text_content: textContent,
      chat_history: chatHistory.map(m => ({ role: m.role, content: m.content }))
    }),
  });

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }

  return response.json();
};
