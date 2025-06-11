<script setup lang="ts">
import type { PropType } from 'vue';

import { onMounted, onUnmounted, ref, watch } from 'vue';

import { Modal } from 'ant-design-vue';

import FolderSelect from '../FolderSelect/index.vue';
import { getQuarkShareFileListApi } from './api';

const props = defineProps({
  item: {
    type: Object as PropType<any>,
    default: () => ({}),
  },
});
const fileList = ref<any[]>([]);
const open = defineModel<boolean>('open', {
  default: false,
  type: Boolean,
});

const width = ref('800px');

const updateWidth = () => {
  const w = window.innerWidth;
  if (w < 640) {
    width.value = '90vw';
  } else if (w < 768) {
    width.value = '800px';
  } else if (w < 1024) {
    width.value = '1000px';
  } else if (w < 1280) {
    width.value = '1000px';
  } else {
    width.value = '1000px';
  }
};

onMounted(() => {
  updateWidth();
  window.addEventListener('resize', updateWidth);
});

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth);
});

const getQuarkShareFileList = async () => {
  const res = await getQuarkShareFileListApi({
    share_url: props.item?.cloudLinks?.[0],
  });
  fileList.value = res.list;
};

watch(open, (value) => {
  if (value) {
    getQuarkShareFileList();
  }
});
</script>

<template>
  <Modal v-model:open="open" title="分享文件" :width="width">
    <FolderSelect :file-list="fileList" />
  </Modal>
</template>
