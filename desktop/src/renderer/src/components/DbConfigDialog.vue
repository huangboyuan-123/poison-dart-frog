<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

const props = defineProps<{ config: DbConfig | null }>()
const emit = defineEmits<{ save: [cfg: DbConfig]; close: [] }>()

const form = reactive<DbConfig>({
  id: '', name: '', type: 'mysql', host: 'localhost', port: 3306,
  user: 'root', password: '', database: 'sqlagent',
})

onMounted(() => {
  if (props.config) Object.assign(form, { ...props.config, password: '' })
})

const saving = ref(false)
async function onSave() {
  saving.value = true
  emit('save', { ...form })
  saving.value = false
}

const dbTypes = [
  { label: 'MySQL', value: 'mysql' },
  { label: 'PostgreSQL', value: 'postgresql' },
  { label: 'SQL Server', value: 'sqlserver' },
  { label: 'SQLite', value: 'sqlite' },
]

const defaultPorts: Record<string, number> = { mysql: 3306, postgresql: 5432, sqlserver: 1433, sqlite: 0 }

function onTypeChange(t: string) {
  form.port = defaultPorts[t] || 3306
}
</script>

<template>
  <el-dialog :model-value="true" title="数据库连接配置" width="460" @close="emit('close')">
    <el-form :model="form" label-width="80px" label-position="left" size="default">
      <el-form-item label="名称">
        <el-input v-model="form.name" placeholder="我的数据库" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="form.type" @change="onTypeChange">
          <el-option v-for="t in dbTypes" :key="t.value" :label="t.label" :value="t.value" />
        </el-select>
      </el-form-item>
      <template v-if="form.type !== 'sqlite'">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item label="地址">
              <el-input v-model="form.host" placeholder="localhost" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="端口" label-width="50px">
              <el-input-number v-model="form.port" :min="1" :max="65535" controls-position="right" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="用户名">
          <el-input v-model="form.user" placeholder="root" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="数据库密码" show-password />
        </el-form-item>
      </template>
      <el-form-item label="数据库">
        <el-input v-model="form.database" placeholder="sqlagent" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('close')">取消</el-button>
      <el-button type="primary" :loading="saving" @click="onSave">保存连接</el-button>
    </template>
  </el-dialog>
</template>
