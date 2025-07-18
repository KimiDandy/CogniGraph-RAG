/**
 * Uploads a file to the backend and returns the extracted text.
 * @param file The file to upload.
 * @returns The JSON response from the API.
 */
export async function uploadAndParseFile(file: File): Promise<{ filename: string; extracted_text: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch('http://127.0.0.1:8000/uploadfile/', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred.' }));
    throw new Error(errorData.detail || 'Failed to upload and parse file.');
  }

  return response.json();
}
