<script setup lang="ts">
import type { PropType } from 'vue';

import { ref, watch } from 'vue';

import { MdiFile, MdiFolder, MdiHome } from '@vben/icons';

import {
  Breadcrumb,
  BreadcrumbItem,
  Checkbox,
  CheckboxGroup,
} from 'ant-design-vue';

const props = defineProps({
  fileList: {
    type: Array as PropType<any[]>,
    default: () => [],
  },
  paths: {
    type: Array as PropType<any[]>,
    default: () => [],
  },
  ifUseCheckbox: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(['navigateTo']);
const selectedFile = defineModel<any[]>('selectedFile', {
  default: () => [],
});
const selectedFileFids = ref<any[]>([]);
const selectAll = ref<boolean>(false);

watch(selectAll, (value) => {
  selectedFile.value = value ? props.fileList : [];
  selectedFileFids.value = value ? props.fileList.map((item) => item.fid) : [];
});

watch(selectedFileFids, (value) => {
  selectedFile.value = props.fileList.filter((item) =>
    value.includes(item.fid),
  );
});

const navigateTo = (file: any) => {
  if (file.dir) {
    emit('navigateTo', { fid: file.fid, name: file.file_name });
  }
};
</script>
<template>
  <div>
    <div>
      <Breadcrumb>
        <BreadcrumbItem class="cursor-pointer" @click="emit('navigateTo', {})">
          <MdiHome class="inline-block text-xl" />
        </BreadcrumbItem>
        <BreadcrumbItem
          v-for="path in paths"
          :key="path.fid"
          class="cursor-pointer"
          @click="emit('navigateTo', { fid: path.fid, name: path.name })"
        >
          {{ path.name }}
        </BreadcrumbItem>
      </Breadcrumb>
    </div>
    <div class="mt-4 border-b border-t">
      <div class="ml-5 mt-3 w-full" v-if="ifUseCheckbox">
        <Checkbox v-model:checked="selectAll"> 全选 </Checkbox>
      </div>
      <div class="p-3">
        <CheckboxGroup v-model:value="selectedFileFids" class="w-full">
          <div
            class="flex min-h-[50px] w-full cursor-pointer items-center rounded-lg border"
            v-for="file in fileList"
            :key="file.fid"
          >
            <Checkbox :value="file.fid" class="ml-2" v-if="ifUseCheckbox" />
            <MdiFolder
              class="ml-2 mr-2 text-2xl"
              v-if="file.dir"
              @click="navigateTo(file)"
            />
            <MdiFile
              class="ml-2 mr-2 text-2xl"
              v-if="file.file"
              @click="navigateTo(file)"
            />
            <div
              class="h-full w-[calc(100%-25px)] truncate leading-[50px]"
              @click="navigateTo(file)"
            >
              {{ file.file_name }}
            </div>
          </div>
        </CheckboxGroup>
      </div>
    </div>
  </div>
</template>
