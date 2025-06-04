/**
 * Personal Information Section Component
 * Displays AI-extracted personal information from processed documents
 */

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  Brain, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  FileText, 
  User, 
  Phone, 
  MapPin, 
  CreditCard,
  Calendar,
  Download,
  Eye,
  RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import { apiClient } from "@/api/client";

interface ExtractedInfo {
  id: string;
  extracted_first_name?: string;
  extracted_last_name?: string;
  extracted_cnp?: string;
  extracted_address?: string;
  extracted_phone?: string;
  extracted_birth_date?: string;
  extracted_birth_place?: string;
  extracted_nationality?: string;
  extracted_id_series?: string;
  extracted_id_number?: string;
  source_document_type: string;
  extraction_confidence: number;
  is_verified: boolean;
  verification_status: string;
  created_at: string;
  ai_model_used: string;
}

interface ScannedDocument {
  id: string;
  original_filename: string;
  document_type: string;
  title: string;
  description: string;
  confidence_score: number;
  processing_time: number;
  created_at: string;
  ai_model_used: string;
}

interface ProfileCompletion {
  completion_percentage: number;
  missing_fields: string[];
  has_ai_data: boolean;
  has_usable_ai_data: boolean;
  verified_documents: number;
  total_scanned_documents: number;
}

const PersonalInfoSection: React.FC = () => {
  const [extractedInfo, setExtractedInfo] = useState<ExtractedInfo[]>([]);
  const [scannedDocuments, setScannedDocuments] = useState<ScannedDocument[]>([]);
  const [profileCompletion, setProfileCompletion] = useState<ProfileCompletion | null>(null);
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState<string | null>(null);

  useEffect(() => {
    loadAIExtractedData();
  }, []);

  const loadAIExtractedData = async () => {
    try {
      setLoading(true);
      const [profileResponse, extractedResponse, documentsResponse] = await Promise.all([
        apiClient.get('/auto-archive/profile'),
        apiClient.get('/auto-archive/profile/extracted-info'),
        apiClient.get('/auto-archive/profile/documents')
      ]);

      setProfileCompletion(profileResponse.data.completion_status);
      setExtractedInfo(extractedResponse.data.extracted_info);
      setScannedDocuments(documentsResponse.data.documents);
    } catch (error) {
      console.error('Error loading AI extracted data:', error);
      toast.error('Eroare la încărcarea datelor extrase de AI');
    } finally {
      setLoading(false);
    }
  };

  const handleApplyExtractedInfo = async (infoId: string) => {
    try {
      setApplying(infoId);
      await apiClient.put('/auto-archive/profile/update-from-ai', {
        extracted_info_id: infoId,
        use_extracted_first_name: true,
        use_extracted_last_name: true,
        use_extracted_cnp: true,
        use_extracted_address: true,
        use_extracted_phone: true
      });

      toast.success('Informațiile au fost aplicate cu succes în profil!');
      await loadAIExtractedData();
      // Trigger a refresh of the parent component
      window.location.reload();
    } catch (error) {
      console.error('Error applying extracted info:', error);
      toast.error('Eroare la aplicarea informațiilor');
    } finally {
      setApplying(null);
    }
  };

  const handleVerifyInfo = async (infoId: string, isApproved: boolean) => {
    try {
      await apiClient.put(`/auto-archive/profile/verify-extracted-info/${infoId}`, {
        is_approved: isApproved,
        notes: isApproved ? 'Informații verificate și aprobate' : 'Informații respinse de utilizator'
      });

      toast.success(isApproved ? 'Informațiile au fost aprobate' : 'Informațiile au fost respinse');
      await loadAIExtractedData();
    } catch (error) {
      console.error('Error verifying info:', error);
      toast.error('Eroare la verificarea informațiilor');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ro-RO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status: string, isVerified: boolean) => {
    if (isVerified) {
      return <Badge variant="success" className="bg-green-100 text-green-800">Verificat</Badge>;
    }
    switch (status) {
      case 'pending':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">În așteptare</Badge>;
      case 'approved':
        return <Badge variant="success" className="bg-green-100 text-green-800">Aprobat</Badge>;
      case 'rejected':
        return <Badge variant="destructive" className="bg-red-100 text-red-800">Respins</Badge>;
      default:
        return <Badge variant="outline">Necunoscut</Badge>;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <RefreshCw className="h-6 w-6 animate-spin mr-2" />
            <span>Se încarcă informațiile extrase de AI...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Profile Completion Overview */}
      {profileCompletion && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-blue-600" />
              Status completare profil cu AI
            </CardTitle>
            <CardDescription>
              Progresul completării profilului tău cu ajutorul inteligenței artificiale
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-1">
                  {profileCompletion.completion_percentage}%
                </div>
                <div className="text-sm text-gray-600">Completare profil</div>
                <Progress value={profileCompletion.completion_percentage} className="mt-2" />
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-1">
                  {profileCompletion.verified_documents}
                </div>
                <div className="text-sm text-gray-600">Documente verificate</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-1">
                  {profileCompletion.total_scanned_documents}
                </div>
                <div className="text-sm text-gray-600">Documente scanate</div>
              </div>
            </div>
            
            {profileCompletion.has_usable_ai_data && (
              <Alert className="mt-4 bg-green-50 border-green-200">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">
                  AI-ul a detectat informații care pot completa profilul tău. Vezi secțiunea de mai jos pentru a le aplica.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* AI Extracted Information */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Informații personale extrase de AI
          </CardTitle>
          <CardDescription>
            Informațiile tale personale detectate automat din documentele scanate
          </CardDescription>
        </CardHeader>
        <CardContent>
          {extractedInfo.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p>Nu există încă informații extrase din documente.</p>
              <p className="text-sm">Scanează un document de identitate pentru a începe.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {extractedInfo.map((info, index) => (
                <Card key={info.id} className="border-gray-200">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-10 w-10">
                          <AvatarFallback>
                            <FileText className="h-5 w-5" />
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <h4 className="font-medium">
                            {info.source_document_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </h4>
                          <p className="text-sm text-gray-500">
                            Extras pe {formatDate(info.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium ${getConfidenceColor(info.extraction_confidence)}`}>
                          {Math.round(info.extraction_confidence * 100)}% încredere
                        </span>
                        {getStatusBadge(info.verification_status, info.is_verified)}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      {info.extracted_first_name && (
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">Prenume:</span>
                          <span className="font-medium">{info.extracted_first_name}</span>
                        </div>
                      )}
                      {info.extracted_last_name && (
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">Nume:</span>
                          <span className="font-medium">{info.extracted_last_name}</span>
                        </div>
                      )}
                      {info.extracted_cnp && (
                        <div className="flex items-center gap-2">
                          <CreditCard className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">CNP:</span>
                          <span className="font-medium">{info.extracted_cnp}</span>
                        </div>
                      )}
                      {info.extracted_phone && (
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">Telefon:</span>
                          <span className="font-medium">{info.extracted_phone}</span>
                        </div>
                      )}
                      {info.extracted_address && (
                        <div className="flex items-center gap-2 md:col-span-2">
                          <MapPin className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">Adresă:</span>
                          <span className="font-medium">{info.extracted_address}</span>
                        </div>
                      )}
                      {info.extracted_birth_date && (
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-gray-400" />
                          <span className="text-sm text-gray-600">Data nașterii:</span>
                          <span className="font-medium">{info.extracted_birth_date}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t">
                      <div className="text-xs text-gray-500">
                        Model AI: {info.ai_model_used}
                      </div>
                      <div className="flex gap-2">
                        {!info.is_verified && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleVerifyInfo(info.id, false)}
                            >
                              <AlertCircle className="h-4 w-4 mr-1" />
                              Respinge
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleVerifyInfo(info.id, true)}
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Verifică
                            </Button>
                          </>
                        )}
                        <Button
                          variant="default"
                          size="sm"
                          onClick={() => handleApplyExtractedInfo(info.id)}
                          disabled={applying === info.id}
                        >
                          {applying === info.id ? (
                            <>
                              <RefreshCw className="h-4 w-4 mr-1 animate-spin" />
                              Se aplică...
                            </>
                          ) : (
                            <>
                              <Download className="h-4 w-4 mr-1" />
                              Aplică în profil
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scanned Documents Summary */}
      {scannedDocuments.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Documentele tale scanate ({scannedDocuments.length})
            </CardTitle>
            <CardDescription>
              Istoric al documentelor procesate cu AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {scannedDocuments.slice(0, 5).map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="h-5 w-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-sm">{doc.title}</p>
                      <p className="text-xs text-gray-500">{doc.description}</p>
                      <p className="text-xs text-gray-400">
                        {formatDate(doc.created_at)} • {Math.round(doc.confidence_score * 100)}% încredere
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {doc.document_type}
                  </Badge>
                </div>
              ))}
              {scannedDocuments.length > 5 && (
                <p className="text-sm text-gray-500 text-center">
                  ... și încă {scannedDocuments.length - 5} documente
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PersonalInfoSection;
