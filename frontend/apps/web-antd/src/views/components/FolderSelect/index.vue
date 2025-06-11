<script setup lang="ts">
import type { PropType } from 'vue';

import { watch } from 'vue';

import { MdiFolder } from '@vben/icons';

import { Breadcrumb, BreadcrumbItem } from 'ant-design-vue';

const props = defineProps({
  fileList: {
    type: Array as PropType<any[]>,
    default: () => [],
  },
});

watch(
  () => props.fileList,
  (value) => {
    console.error(value);
  },
);
</script>
<template>
  <div>
    <div>
      <Breadcrumb>
        <BreadcrumbItem>Home</BreadcrumbItem>
        <BreadcrumbItem>Application Center</BreadcrumbItem>
        <BreadcrumbItem>Application List</BreadcrumbItem>
        <BreadcrumbItem>An Application</BreadcrumbItem>
      </Breadcrumb>
    </div>
    <div class="mt-4 border-b border-t">
      <div class="p-3">
        <div class="flex min-h-[50px] w-full items-center rounded-lg border">
          <MdiFolder class="ml-2 mr-2 text-2xl" />
          <div class="truncate">{{ props.fileList[0]?.file_name }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
