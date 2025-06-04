const BASE_URL = '/api/auto-archive';

/**
 * Get authentication token from localStorage
 */
function getAuthToken(): string | null {
  return localStorage.getItem('authToken');
}

/**
 * Get auth headers for API requests
 */
function getAuthHeaders(): HeadersInit {
  const token = getAuthToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

export interface AutoArchiveMetadata {
  title: string;
  category: string;
  authority: string;
  document_type: string;
  issue_date?: string;
  document_number?: string;
  description?: string;
  tags?: string[];
  confidence_score?: number;
}

export interface AutoArchiveResponse {
  success: boolean;
  document_id?: string;
  metadata?: AutoArchiveMetadata;
  file_path?: string;
  error?: string;
  refresh_archive?: boolean;
  category_info?: {
    category_name: string;
  };
  message?: string;
}

export interface ArchivedDocument {
  document_id: number;
  filename: string;
  document_type: string;
  transcribed_text: string;
  scan_date: string;
  created_at: string;
}

export const autoArchiveApi = {
  /**
   * Upload PDF and auto-generate archival metadata using Gemini API
   */
  async uploadPdfForAutoArchive(
    file: File,
    documentType?: string
  ): Promise<AutoArchiveResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (documentType) {
      formData.append('document_type', documentType);
    }

    const response = await fetch(`${BASE_URL}/upload-pdf`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    // Trigger archive refresh if successful
    if (result.success && result.refresh_archive) {
      // Dispatch custom event to notify archive components
      window.dispatchEvent(new CustomEvent('archiveUpdated', {
        detail: {
          documentId: result.document_id,
          categoryInfo: result.category_info,
          message: result.message
        }
      }));
      
      console.log('📁 Archive updated:', result.category_info?.category_name);
    }

    return result;
  },

  /**
   * Scan from printer and automatically archive with metadata extraction
   */
  async scanAndAutoArchive(documentType?: string): Promise<AutoArchiveResponse> {
    // Create headers with auth but without Content-Type (let browser handle FormData boundary)
    const headers = getAuthHeaders();
    
    // Create request options based on whether we have document_type
    let requestOptions: RequestInit;
    
    if (documentType && documentType.trim()) {
      // Send FormData if we have document_type
      const formData = new FormData();
      formData.append('document_type', documentType.trim());
      
      requestOptions = {
        method: 'POST',
        headers: headers,
        body: formData,
      };
    } else {
      // Send empty FormData to ensure proper content-type
      const formData = new FormData();
      // Append an empty string to ensure FormData is valid
      formData.append('document_type', '');
      
      requestOptions = {
        method: 'POST',
        headers: headers,
        body: formData,
      };
    }

    const response = await fetch(`${BASE_URL}/scan-and-archive`, requestOptions);

    if (!response.ok) {
      let errorMessage = `Scan failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch (parseError) {
        // If response is not JSON, check if it's an auth error
        if (response.status === 401) {
          errorMessage = "Authentication required. Please log in.";
        } else if (response.status === 403) {
          errorMessage = "Access denied. Official role required.";
        } else if (response.status === 400) {
          errorMessage = "Invalid request. Please check your input.";
        } else {
          errorMessage = response.statusText || errorMessage;
        }
      }
      throw new Error(errorMessage);
    }

    const result = await response.json();
    
    // Trigger archive refresh if successful
    if (result.success && result.refresh_archive) {
      // Dispatch custom event to notify archive components
      window.dispatchEvent(new CustomEvent('archiveUpdated', {
        detail: {
          documentId: result.document_id,
          categoryInfo: result.category_info,
          message: result.message
        }
      }));
      
      console.log('📁 Archive updated:', result.category_info?.category_name);
    }

    return result;
  },

  /**
   * Get auto-generated metadata for a document
   */
  async getAutoArchiveMetadata(docId: number): Promise<ArchivedDocument> {
    const response = await fetch(`${BASE_URL}/metadata/${docId}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  /**
   * List recent auto-archived documents
   */
  async listAutoArchivedDocuments(limit: number = 20): Promise<{
    documents: ArchivedDocument[];
    total: number;
  }> {
    const response = await fetch(`${BASE_URL}/list?limit=${limit}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Check API health and capabilities
   */
  async getServiceInfo(): Promise<{
    message: string;
    version: string;
    features: {
      basic_scanning: boolean;
      ocr_processing: boolean;
      auto_archive_upload: boolean;
      auto_archive_scan: boolean;
    };
    naps2_found: boolean;
    ocr_enabled: boolean;
  }> {
    const response = await fetch(`${BASE_URL}/info`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  },

  /**
   * Get category statistics for auto-archive
   */
  async getCategoryStats(): Promise<{
    success: boolean;
    total_categories: number;
    max_categories: number;
    categories_remaining: number;
    categories: Array<{
      id: string;
      name: string;
      description: string;
      document_count: number;
      created_at: string;
    }>;
    auto_archive_info: {
      similarity_threshold: number;
      matching_enabled: boolean;
      auto_creation_enabled: boolean;
    };
  }> {
    const response = await fetch(`${BASE_URL}/category-stats`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  },
}; 