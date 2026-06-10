<template>
  <div class="markdown" v-html="html"></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const props = defineProps<{ content: string }>()
const html = computed(() => DOMPurify.sanitize(marked(props.content, { breaks: true }) as string))
</script>
