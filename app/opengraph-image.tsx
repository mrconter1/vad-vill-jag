import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = 'Vilket parti tillhör jag? – Riksdagsquiz'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          background: '#F7F3EC',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '80px',
          fontFamily: 'serif',
        }}
      >
        {/* Top accent bar */}
        <div style={{ display: 'flex', gap: 12 }}>
          <div style={{ width: 60, height: 6, background: '#FCA311' }} />
          <div style={{ width: 20, height: 6, background: '#14213D', opacity: 0.2 }} />
        </div>

        {/* Main title */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div
            style={{
              fontSize: 96,
              fontWeight: 900,
              color: '#14213D',
              lineHeight: 0.95,
              letterSpacing: '-2px',
            }}
          >
            VILKET PARTI
          </div>
          <div
            style={{
              fontSize: 96,
              fontWeight: 900,
              color: '#FCA311',
              lineHeight: 0.95,
              letterSpacing: '-2px',
            }}
          >
            TILLHÖR JAG?
          </div>
          <div
            style={{
              fontSize: 28,
              color: '#14213D',
              opacity: 0.5,
              fontWeight: 400,
              marginTop: 8,
            }}
          >
            Riksdagsquiz baserat på verkliga voteringar de senaste fem åren
          </div>
        </div>

        {/* Bottom: party labels */}
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {[
            ['S', '#E8112D'],
            ['SD', '#0047A3'],
            ['M', '#52BDEC'],
            ['V', '#C50A0A'],
            ['C', '#009933'],
            ['KD', '#231F72'],
            ['MP', '#83CF39'],
            ['L', '#6BB7E0'],
          ].map(([party, color]) => (
            <div
              key={party}
              style={{
                fontSize: 22,
                fontWeight: 900,
                color,
                padding: '6px 14px',
                border: `2px solid ${color}`,
                opacity: 0.7,
              }}
            >
              {party}
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size },
  )
}
