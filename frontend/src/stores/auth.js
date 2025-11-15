import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:9910'

export const api = axios.create({ baseURL: API_BASE })
let interceptorsAttached = false

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: localStorage.getItem('fm_token') || null,
        email: localStorage.getItem('fm_email') || null,
        loading: false,
        error: null,
        pubkeyPem: null,
        pubkeyKey: null,
    }),
    getters: {
        isAuthenticated: (state) => !!state.token,
        authHeaders: (state) => state.token ? { Authorization: `Bearer ${state.token}` } : {},
    },
    actions: {
        async ensureCrypto() {
            if (this.pubkeyKey) return
            try {
                const r = await api.get('/auth/pubkey')
                this.pubkeyPem = r.data?.pem
                if (this.pubkeyPem) {
                    this.pubkeyKey = await importRsaPublicKey(this.pubkeyPem)
                }
            } catch (e) {
                // If fetching/importing key fails, we'll fall back to plaintext
                this.pubkeyKey = null
            }
        },
        ensureInterceptors() {
            if (interceptorsAttached) return
            // Request: inject Authorization header
            api.interceptors.request.use(cfg => {
                if (this.token) {
                    cfg.headers.Authorization = `Bearer ${this.token}`
                }
                return cfg
            })
            // Response: check for refreshed token header
            api.interceptors.response.use(res => {
                const newToken = res.headers['x-new-token'] || res.headers['X-New-Token']
                if (newToken && newToken !== this.token) {
                    this.token = newToken
                    localStorage.setItem('fm_token', newToken)
                }
                return res
            }, err => {
                // Optional: auto-logout on 401 token expired (detail === 'Token expired')
                if (err.response?.status === 401) {
                    const detail = err.response?.data?.detail
                    if (detail === 'Token expired' || detail === 'Could not validate credentials') {
                        this.logout()
                    }
                }
                return Promise.reject(err)
            })
            interceptorsAttached = true
        },
        async login(email, password) {
            this.loading = true
            this.error = null
            try {
                this.ensureInterceptors()
                await this.ensureCrypto()
                let payload = { email, password }
                if (this.pubkeyKey && window.crypto?.subtle) {
                    try {
                        const enc_password = await rsaEncryptToBase64(this.pubkeyKey, password)
                        payload = { email, enc_password }
                    } catch (_) {
                        // fall back to plaintext
                    }
                }
                const r = await api.post(`/auth/login`, payload)
                this.token = r.data.access_token
                this.email = email
                localStorage.setItem('fm_token', this.token)
                localStorage.setItem('fm_email', this.email)
            } catch (e) {
                this.error = e.response?.data?.detail || e.message
                throw e
            } finally {
                this.loading = false
            }
        },
        async register(email, password, companyName = null) {
            this.loading = true
            this.error = null
            try {
                this.ensureInterceptors()
                await this.ensureCrypto()
                let payload = { email, password, company_name: companyName }
                if (this.pubkeyKey && window.crypto?.subtle) {
                    try {
                        const enc_password = await rsaEncryptToBase64(this.pubkeyKey, password)
                        payload = { email, enc_password, company_name: companyName }
                    } catch (_) {
                        // fall back to plaintext
                    }
                }
                await api.post(`/auth/register`, payload)
                await this.login(email, password)
            } catch (e) {
                this.error = e.response?.data?.detail || e.message
                throw e
            } finally {
                this.loading = false
            }
        },
        logout() {
            this.token = null
            this.email = null
            localStorage.removeItem('fm_token')
            localStorage.removeItem('fm_email')
        }
    }
})

// --- Crypto helpers (Web Crypto API: RSA-OAEP-256) ---
function pemToArrayBuffer(pem) {
    const b64 = pem.replace(/-----BEGIN PUBLIC KEY-----/g, '')
        .replace(/-----END PUBLIC KEY-----/g, '')
        .replace(/\s+/g, '')
    const raw = atob(b64)
    const arr = new Uint8Array(raw.length)
    for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i)
    return arr.buffer
}

async function importRsaPublicKey(pem) {
    const spki = pemToArrayBuffer(pem)
    return await window.crypto.subtle.importKey(
        'spki',
        spki,
        { name: 'RSA-OAEP', hash: 'SHA-256' },
        false,
        ['encrypt']
    )
}

async function rsaEncryptToBase64(publicKey, text) {
    const data = new TextEncoder().encode(text)
    const buf = await window.crypto.subtle.encrypt({ name: 'RSA-OAEP' }, publicKey, data)
    const bytes = new Uint8Array(buf)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
    return btoa(binary)
}
