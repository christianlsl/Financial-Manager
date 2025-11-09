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
      <h2>采购</h2>
      <form @submit.prevent="create">
        <label>日期</label>
        <input v-model="form.date" type="date" required />
        <label>供应商名称</label>
        <input v-model="form.supplier_name" required />
        <label>项目数</label>
        <input v-model.number="form.items_count" type="number" min="0" required />
        <label>总金额</label>
        <input v-model.number="form.total_amount" type="number" min="0" step="0.01" required />
        <label>状态</label>
        <select v-model="form.status">
          <option value="pending">待处理</option>
          <option value="ordered">已下单</option>
          <option value="received">已收货</option>
        </select>
        <label>备注</label>
        <textarea v-model="form.notes"></textarea>
        <button type="submit">创建</button>
      </form>
      <p v-if="error" style="color:red">{{ error }}</p>
      <table v-if="items.length">
        <thead>
          <tr>
            <th>ID</th><th>日期</th><th>供应商</th><th>项目数</th><th>金额</th><th>状态</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in items" :key="p.id">
            <td>{{ p.id }}</td>
            <td>{{ p.date }}</td>
            <td>{{ p.supplier_name }}</td>
            <td>{{ p.items_count }}</td>
            <td>{{ p.total_amount }}</td>
            <td>{{ p.status }}</td>
            <td><button @click="remove(p.id)">删除</button></td>
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
  supplier_name: '',
  items_count: 0,
  total_amount: 0,
  status: 'pending',
  notes: ''
})

function logout(){ auth.logout(); router.push('/login') }

async function load(){
  try {
    const r = await axios.get(`${API_BASE}/purchases/`, { headers: auth.authHeaders })
    items.value = r.data
  } catch(e){ error.value = e.response?.data?.detail || e.message }
}

async function create(){
  try {
    await axios.post(`${API_BASE}/purchases/`, { ...form }, { headers: auth.authHeaders })
    await load()
  } catch(e){ error.value = e.response?.data?.detail || e.message }
}

async function remove(id){
  try {
    await axios.delete(`${API_BASE}/purchases/${id}`, { headers: auth.authHeaders })
    items.value = items.value.filter(i => i.id !== id)
  } catch(e){ error.value = e.response?.data?.detail || e.message }
}

onMounted(load)
</script>
