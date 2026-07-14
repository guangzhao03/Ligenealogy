<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import AmapPicker from '@/components/map/AmapPicker.vue'
import {
  createGeoPlace,
  deleteGeoPlace,
  fetchGeoPlaces,
  updateGeoPlace,
} from '@/api/geoPlace'
import { fetchPersons } from '@/api/person'
import type { GeoPlace, GeoPlaceType, Person } from '@/types'
import { useFamilyStore } from '@/stores/family'

const familyStore = useFamilyStore()
const loading = ref(false)
const places = ref<GeoPlace[]>([])
const persons = ref<Person[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const filterType = ref<GeoPlaceType | ''>('')

const form = reactive({
  place_type: 'distribution' as GeoPlaceType,
  name: '',
  longitude: undefined as number | undefined,
  latitude: undefined as number | undefined,
  address: '',
  description: '',
  related_person_id: undefined as number | undefined,
})

const hasFamily = computed(() => !!familyStore.currentFamily)

const typeText: Record<GeoPlaceType, string> = {
  distribution: '族群分布',
  cemetery: '坟地',
}

async function loadPlaces() {
  if (!familyStore.currentFamily) return
  loading.value = true
  try {
    places.value = await fetchGeoPlaces({
      family_id: familyStore.currentFamily.id,
      place_type: filterType.value || undefined,
    })
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载失败')
  } finally {
    loading.value = false
  }
}

async function loadPersons() {
  if (!familyStore.currentFamily) return
  try {
    const data = await fetchPersons({
      family_id: familyStore.currentFamily.id,
      page: 1,
      page_size: 100,
    })
    persons.value = data.items
  } catch {
    persons.value = []
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    place_type: 'distribution',
    name: '',
    longitude: 112.52832,
    latitude: 32.99076,
    address: '',
    description: '',
    related_person_id: undefined,
  })
  dialogVisible.value = true
}

function openEdit(place: GeoPlace) {
  editingId.value = place.id
  Object.assign(form, {
    place_type: place.place_type,
    name: place.name,
    longitude: place.longitude,
    latitude: place.latitude,
    address: place.address || '',
    description: place.description || '',
    related_person_id: place.related_person_id ?? undefined,
  })
  dialogVisible.value = true
}

function handlePick(payload: { longitude: number; latitude: number }) {
  form.longitude = Number(payload.longitude.toFixed(6))
  form.latitude = Number(payload.latitude.toFixed(6))
}

async function savePlace() {
  if (!familyStore.currentFamily) return
  if (!form.name.trim()) {
    ElMessage.warning('请填写地点名称')
    return
  }
  if (form.longitude == null || form.latitude == null) {
    ElMessage.warning('请填写或点选经纬度')
    return
  }

  const payload = {
    place_type: form.place_type,
    name: form.name.trim(),
    longitude: form.longitude,
    latitude: form.latitude,
    address: form.address.trim() || undefined,
    description: form.description.trim() || undefined,
    related_person_id: form.related_person_id ?? null,
  }

  try {
    if (editingId.value) {
      await updateGeoPlace(editingId.value, payload)
      ElMessage.success('更新成功')
    } else {
      await createGeoPlace({
        family_id: familyStore.currentFamily.id,
        ...payload,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadPlaces()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存失败')
  }
}

async function removePlace(place: GeoPlace) {
  try {
    await ElMessageBox.confirm(`确认删除「${place.name}」？`, '删除确认', {
      type: 'warning',
    })
    await deleteGeoPlace(place.id)
    ElMessage.success('已删除')
    await loadPlaces()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error instanceof Error ? error.message : '删除失败')
    }
  }
}

onMounted(async () => {
  await familyStore.ensureFamilySelected()
  await Promise.all([loadPlaces(), loadPersons()])
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1>地理标记</h1>
        <p class="subtitle">手工维护族群分布点与坟地位置，展示于门户地图</p>
      </div>
      <el-button type="primary" :disabled="!hasFamily" @click="openCreate">新增标记</el-button>
    </div>

    <div class="toolbar">
      <el-radio-group v-model="filterType" size="small" @change="loadPlaces">
        <el-radio-button value="">全部</el-radio-button>
        <el-radio-button value="distribution">族群分布</el-radio-button>
        <el-radio-button value="cemetery">坟地</el-radio-button>
      </el-radio-group>
      <el-button @click="loadPlaces">刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="places" stripe>
      <el-table-column prop="name" label="名称" min-width="160" />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">{{ typeText[row.place_type as GeoPlaceType] }}</template>
      </el-table-column>
      <el-table-column label="经度" width="120">
        <template #default="{ row }">{{ row.longitude }}</template>
      </el-table-column>
      <el-table-column label="纬度" width="120">
        <template #default="{ row }">{{ row.latitude }}</template>
      </el-table-column>
      <el-table-column prop="address" label="地址" min-width="160" show-overflow-tooltip />
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="danger" @click="removePlace(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑地理标记' : '新增地理标记'"
      width="720px"
      destroy-on-close
    >
      <el-form label-width="96px">
        <el-form-item label="类型" required>
          <el-radio-group v-model="form.place_type">
            <el-radio value="distribution">族群分布</el-radio>
            <el-radio value="cemetery">坟地</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" maxlength="100" placeholder="地点名称" />
        </el-form-item>
        <el-form-item label="经度" required>
          <el-input-number v-model="form.longitude" :precision="6" :step="0.0001" :controls="false" style="width: 100%" />
        </el-form-item>
        <el-form-item label="纬度" required>
          <el-input-number v-model="form.latitude" :precision="6" :step="0.0001" :controls="false" style="width: 100%" />
        </el-form-item>
        <el-form-item label="地图点选">
          <AmapPicker
            :longitude="form.longitude"
            :latitude="form.latitude"
            @pick="handlePick"
          />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" maxlength="200" placeholder="可选文字地址" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="可选说明" />
        </el-form-item>
        <el-form-item label="关联人物">
          <el-select
            v-model="form.related_person_id"
            clearable
            filterable
            placeholder="可选"
            style="width: 100%"
          >
            <el-option
              v-for="person in persons"
              :key="person.id"
              :label="`${person.name}（${person.nickname}）`"
              :value="person.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePlace">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.page-header h1 {
  margin: 0;
  font-size: 22px;
  color: #1b3428;
}

.subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7a71;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>
