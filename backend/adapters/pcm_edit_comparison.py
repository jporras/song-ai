"""Compare aligned PCM samples; this does not infer perceptual musical fidelity."""
import math
import struct
import wave
from pathlib import Path
from adapters.sample_audio_evidence import inspect_sample_wav


def compare_pcm_edit(source: Path, candidate: Path, start: float, end: float) -> dict:
    source_info = inspect_sample_wav(source, source.parent)
    candidate_info = inspect_sample_wav(candidate, candidate.parent)
    fields = ('sample_rate', 'channels', 'sample_width', 'frames')
    result = {'scope':'aligned_pcm_not_perceptual_fidelity',
              'source_sha256':source_info['sha256'], 'candidate_sha256':candidate_info['sha256'],
              'quality_verified':False}
    if any(source_info[k] != candidate_info[k] for k in fields) or source_info['sample_width'] != 2:
        return {**result, 'status':'not_comparable', 'reason':'Requires equal-length PCM16 with equal rate and channels'}
    duration = source_info['duration_seconds']
    if not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end <= duration:
        raise ValueError('Intervalo fuera del audio comparable.')
    rate, channels = source_info['sample_rate'], source_info['channels']
    regions = []
    with wave.open(str(source),'rb') as a, wave.open(str(candidate),'rb') as b:
        for name, low, high in [('before',0,start),('selected',start,end),('after',end,duration)]:
            first, stop = round(low*rate), round(high*rate)
            if first == stop:
                continue
            a.setpos(first); b.setpos(first)
            remaining=stop-first
            squares=0; count=0; equal=0; peak=0
            while remaining:
                frames=min(remaining,16384)
                for (x,), (y,) in zip(struct.iter_unpack('<h',a.readframes(frames)),struct.iter_unpack('<h',b.readframes(frames))):
                    difference=x-y
                    squares+=difference*difference; equal+=difference==0
                    peak=max(peak,abs(difference)); count+=1
                remaining-=frames
            regions.append({'region':name,'start_seconds':low,'end_seconds':high,
                            'sample_values':count,'expected_sample_values':(stop-first)*channels,
                            'identical_sample_fraction':equal/count,
                            'difference_rms_full_scale':math.sqrt(squares/count)/32768,
                            'maximum_difference_full_scale':peak/32768})
    if inspect_sample_wav(source,source.parent) != source_info or inspect_sample_wav(candidate,candidate.parent) != candidate_info:
        raise ValueError('El audio cambió durante la comparación.')
    return {**result,'status':'measured','regions':regions}
