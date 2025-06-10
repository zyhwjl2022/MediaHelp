<script setup lang="ts">
import { getHotMovieListApi } from './api';
import MediaCardList from './components/MediaCardList.vue';

defineOptions({
  name: 'DoubanHotMovie',
});
</script>
<template>
  <div>
    <MediaCardList :api="getHotMovieListApi" :params="{}" />
  </div>
</template>
