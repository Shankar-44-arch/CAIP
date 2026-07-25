// CAIP-Karnataka — API Service Layer
import axios, { type AxiosInstance, type AxiosError } from 'axios';
import type { KarnatakaCrimeReport, District, DisabledFeature } from '@/types';

let rawApiUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1';
if (rawApiUrl && !rawApiUrl.startsWith('http://') && !rawApiUrl.startsWith('https://') && !rawApiUrl.startsWith('/')) {
  rawApiUrl = `https://${rawApiUrl}`;
}
if (rawApiUrl.startsWith('http') && !rawApiUrl.includes('/api/v1')) {
  rawApiUrl = `${rawApiUrl.replace(/\/$/, '')}/api/v1`;
}
const API_BASE_URL = rawApiUrl;

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({ baseURL: API_BASE_URL, timeout: 30000 });

    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('caip_access_token');
      if (token) config.headers.Authorization = `Bearer ${token}`;
      return config;
    });

    this.client.interceptors.response.use(
      (res) => res,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('caip_access_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async login(username: string, password: string) {
    const { data } = await this.client.post('/auth/login', { username, password });
    localStorage.setItem('caip_access_token', data.access_token);
    return data;
  }

  async signup(payload: { email: string; username: string; full_name: string; password: string; role?: string }) {
    if (!payload.role) {
      payload.role = 'analyst';
    }
    const { data } = await this.client.post('/auth/register', payload);
    return data;
  }

  async getMe() {
    const { data } = await this.client.get('/auth/me');
    return data;
  }

  async getFullReport(params?: { district_code?: string; year?: number }) {
    const { data } = await this.client.get<KarnatakaCrimeReport>('/intelligence/report', { params });
    return data;
  }

  async getDistrictRanking(params?: { year?: number, ranking_basis?: string }) {
    const { data } = await this.client.get('/intelligence/district-ranking', { params });
    return data;
  }

  async getCrimeCategories(params?: { district_code?: string; year?: number }) {
    const { data } = await this.client.get('/intelligence/crime-categories', { params });
    return data;
  }

  async getTrend(params?: { district_code?: string }) {
    const { data } = await this.client.get('/intelligence/trend', { params });
    return data;
  }

  async listDistricts() {
    const { data } = await this.client.get<District[]>('/districts');
    return data;
  }

  async listFeatureFlags() {
    const { data } = await this.client.get<{ flag_key: string; is_enabled: boolean; reason: string }[]>(
      '/feature-flags'
    );
    return data;
  }

  async listAvailableYears() {
    const { data } = await this.client.get<{ years_available: number[] }>('/data-years');
    return data;
  }
  async uploadCSV(formData: FormData) {
    return await this.client.post('/etl/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async uploadPDF(formData: FormData) {
    return await this.client.post('/intelligence/upload-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000,
    });
  }

  async getNetworkData() {
    const { data } = await this.client.get('/intelligence/network');
    return data;
  }

  async getOffendersData() {
    const { data } = await this.client.get('/intelligence/offenders');
    return data;
  }

  async getAnomaliesData() {
    const { data } = await this.client.get('/intelligence/anomalies');
    return data;
  }

  async getSocioEconomicData() {
    const { data } = await this.client.get('/intelligence/socioeconomic');
    return data;
  }
}

export const apiClient = new ApiClient();
