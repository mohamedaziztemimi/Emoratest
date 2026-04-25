import { ImageResponse } from 'next/og'

export const size = { width: 180, height: 180 }
export const contentType = 'image/png'

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div style={{
        fontSize: 110,
        background: '#007BFF',
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        borderRadius: 38,
        fontWeight: 700,
        fontFamily: 'Arial, sans-serif',
      }}>
        E
      </div>
    ),
    { ...size }
  )
}
