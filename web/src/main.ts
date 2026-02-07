import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  ElAlert,
  ElAside,
  ElAvatar,
  ElButton,
  ElCard,
  ElCol,
  ElContainer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElHeader,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElLoading,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElOption,
  ElPagination,
  ElRow,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus'
import 'element-plus/dist/index.css'
import './style.css'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.component(ElAlert.name!, ElAlert)
app.component(ElAside.name!, ElAside)
app.component(ElAvatar.name!, ElAvatar)
app.component(ElButton.name!, ElButton)
app.component(ElCard.name!, ElCard)
app.component(ElCol.name!, ElCol)
app.component(ElContainer.name!, ElContainer)
app.component(ElDropdown.name!, ElDropdown)
app.component(ElDropdownItem.name!, ElDropdownItem)
app.component(ElDropdownMenu.name!, ElDropdownMenu)
app.component(ElEmpty.name!, ElEmpty)
app.component(ElForm.name!, ElForm)
app.component(ElFormItem.name!, ElFormItem)
app.component(ElHeader.name!, ElHeader)
app.component(ElIcon.name!, ElIcon)
app.component(ElInput.name!, ElInput)
app.component(ElInputNumber.name!, ElInputNumber)
app.component(ElMain.name!, ElMain)
app.component(ElMenu.name!, ElMenu)
app.component(ElMenuItem.name!, ElMenuItem)
app.component(ElOption.name!, ElOption)
app.component(ElPagination.name!, ElPagination)
app.component(ElRow.name!, ElRow)
app.component(ElSelect.name!, ElSelect)
app.component(ElTable.name!, ElTable)
app.component(ElTableColumn.name!, ElTableColumn)
app.component(ElTag.name!, ElTag)
app.directive('loading', ElLoading.directive)

app.mount('#app')
