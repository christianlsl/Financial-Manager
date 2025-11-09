<template>
  <div>
    <nav>
      <strong>Financial Manager</strong>
      <router-link to="/dashboard">总览</router-link>
      <router-link to="/purchases">采购</router-link>
      <router-link to="/sales">销售</router-link>
      <router-link to="/invoices">发票</router-link>
      <span style="flex:1"></span>
      <span>{{ auth.email }}</span>
      <button @click="logout">退出</button>
    </nav>
    <div class="container">
      <h2>销售</h2>
      <form @submit.prevent="create">
        <label>日期</label>
        <input v-model="form.date" type="date" required />
        <label>客户名称</label>
        <input v-model="form.customer_name" required />
        <label>总金额</label>
        <input v-model.number="form.total_amount" type="number" min="0" step="0.01" required />
        <label>状态</label>
        <select v-model="form.status">
          <option value="draft">草稿</option>
          <option value="sent">已发送</option>
          <option value="paid">已支付</option>
        </select>
        <label>备注</label>
        <textarea v-model="form.notes"></textarea>
        <button type="submit">创建</button>
      </form>
      <p v-if="error" style="color:red">{{ error }}</p>
      <table v-if="items.length">
        <thead>
          <tr>
            <th>ID</th><th>日期</th><th>客户</th><th>金额</th><th>状态</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in items" :key="s.id">
            <td>{{ s.id }}</td>
            <td>{{ s.date }}</td>
            <td>{{ s.customer_name }}</td>
            <td>{{ s.total_amount }}</td>
            <td>{{ s.status }}</td>
            <td><button @click="remove(s.id)">删除</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const items = ref([])
const error = ref(null)
const form = reactive({
  date: new Date().toISOString().substring(0,10),
  customer_name: '',
  total_amount: 0,
  status: 'draft',
  notes: ''
})

function logout(){ auth.logout(); router.push('/login') }

async function load(){
  try {
    const r = await axios.get(`${API_BASE}/sales/`, { headers: auth.authHeaders })
    items.value = r.data
  } catch(e){ error.value = e.response?.data?.detail || e.message }
}

async function create(){
  try {
    await axios.post(`${API_BASE}/sales/`, { ...form }, { headers: auth.authHeaders })
    await load()
  } catch(e){ error.value = e.response?.data?.detail || e.message }
}

async function remove(id){
  try {
    await axios.delete(`${API_BASE}/sales/${id}`, { headers: auth.authHeaders })
    items.value = items.value.filter(i => i.id !== id)
  } catch(e){ error.value = e.response?.data?.detail || e.message }
}

onMounted(load)
</script>
