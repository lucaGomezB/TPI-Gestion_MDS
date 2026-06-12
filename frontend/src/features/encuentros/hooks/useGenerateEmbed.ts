import { useMutation } from '@tanstack/react-query';
import { generateEmbed } from '../services/encuentroService';

export function useGenerateEmbed() {
  return useMutation({
    mutationFn: ({ materiaId, formato }: { materiaId: string; formato: 'html' | 'markdown' }) =>
      generateEmbed(materiaId, formato),
  });
}
