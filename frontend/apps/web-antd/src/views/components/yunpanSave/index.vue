<script setup lang="ts">
import type { PropType } from 'vue';

import { computed, onMounted, onUnmounted, ref, watch } from 'vue';

import { Button, Modal } from 'ant-design-vue';

import FolderSelect from '../FolderSelect/index.vue';
import {
  getQuarkFileListApi,
  getQuarkShareFileListApi,
  saveQuarkFileApi,
} from './api';

const props = defineProps({
  item: {
    type: Object as PropType<any>,
    default: () => ({}),
  },
});
const shareUrl = computed(() => {
  return props.item?.cloudLinks?.[0] || '';
});
const fileList = ref<any[]>([]);
const selectedFile = ref<any[]>([]);
const paths = ref<any[]>([]);
const fileList2 = ref<any[]>([]);
const paths2 = ref<any[]>([]);
const open = defineModel<boolean>('open', {
  default: false,
  type: Boolean,
});
const loading = defineModel<boolean>('loading', {
  default: false,
  type: Boolean,
});
const saveOperation = ['分享文件', '保存到'];
const currentStep = ref<number>(0);
const okText = computed(() => {
  return currentStep.value === 0 ? '保存到' : '保存';
});
const modalTitle = computed(() => {
  return saveOperation[currentStep.value];
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

let lastShareUrl: any;
const formatQuarkShareUrl = (dir: any = {}) => {
  const url = lastShareUrl ?? shareUrl.value;
  if (Object.keys(dir).length === 0 || dir.fid === 0) {
    lastShareUrl = url.match(/.*s\/[a-z0-9]+(\?pwd=[^#]+)?/)?.[0] || '';
    return lastShareUrl;
  } else if (url.includes(dir.fid)) {
    lastShareUrl = url.match(new RegExp(`.*/${dir.fid}[^/]*`))?.[0] || '';
    return lastShareUrl;
  } else if (url.includes('#/list/share')) {
    lastShareUrl = `${url}/${dir.fid}-${dir.name?.replace(/-/g, '*101')}`;
    return lastShareUrl;
  } else {
    lastShareUrl = `${url}#/list/share/${dir.fid}-${dir.name?.replace(/-/g, '*101')}`;
    return lastShareUrl;
  }
};

const getShareFileList = async (dir: any = {}) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    const res = await getQuarkShareFileListApi({
      share_url: formatQuarkShareUrl(dir),
    }).finally(() => {
      loading.value = false;
    });
    fileList.value = res.list ?? [];
    paths.value = res.paths ?? [];
  }
};

let filepaths: any[] = [];
const getFileList = async (dir: any = {}) => {
  if (props.item?.cloudType === 'quark') {
    loading.value = true;
    const res = await getQuarkFileListApi({ dir_id: dir.fid }).finally(() => {
      loading.value = false;
    });
    fileList2.value = res.list ?? [];
    if (dir.fid) {
      // 如果当前目录有fid，则将当前目录添加到filepaths中
      const index = filepaths.findIndex((item) => item.fid === dir.fid);
      if (index === -1) {
        filepaths.push(dir);
      } else {
        filepaths = filepaths.slice(0, index + 1);
      }
    } else {
      filepaths = [];
    }
    paths2.value = [...filepaths];
  }
};
watch(open, (value) => {
  if (value) {
    lastShareUrl = undefined;
    fileList.value = [];
    fileList2.value = [];
    paths.value = [];
    paths2.value = [];
    selectedFile.value = [];
    currentStep.value = 0;
    getShareFileList();
  }
});

const navigateTo = (dir: any) => {
  if (currentStep.value === 0) {
    getShareFileList(dir);
  } else {
    getFileList(dir);
  }
};

const onOk = async () => {
  if (currentStep.value === 0) {
    // 下一步
    currentStep.value = 1;
    if (fileList2.value.length === 0) {
      getFileList();
    }
  } else {
    // 保存
    let needSaveFileList: any[] = [];
    needSaveFileList =
      selectedFile.value.length === 0 ? fileList.value : selectedFile.value;
    const file_ids = needSaveFileList.map((item) => item.fid);
    const file_tokens = needSaveFileList.map((item) => item.share_fid_token);
    const target_dir = paths2.value[paths2.value.length - 1]?.fid ?? '0';
    const pdir_fid = paths.value[paths.value.length - 1]?.fid ?? '0';
    await saveQuarkFileApi({
      share_url: shareUrl.value,
      file_ids,
      file_tokens,
      target_dir,
      pdir_fid,
    });
  }
};

const onBack = () => {
  currentStep.value = 0;
};
</script>

<template>
  <Modal v-model:open="open" :title="modalTitle" :width="width">
    <div v-loading="loading" v-show="currentStep === 0">
      <FolderSelect
        v-model:selected-file="selectedFile"
        :file-list="fileList"
        :paths="paths"
        @navigate-to="navigateTo"
      />
    </div>
    <div v-loading="loading" v-show="currentStep === 1">
      <FolderSelect
        :file-list="fileList2"
        :paths="paths2"
        @navigate-to="navigateTo"
      />
    </div>
    <template #footer>
      <Button @click="onBack" v-show="currentStep === 1"> 返回 </Button>
      <Button type="primary" @click="onOk">{{ okText }}</Button>
    </template>
  </Modal>
</template>
