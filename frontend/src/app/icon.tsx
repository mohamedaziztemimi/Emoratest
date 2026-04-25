import { ImageResponse } from 'next/og'

export const size = { width: 48, height: 48 }
export const contentType = 'image/png'

export default function Icon() {
  return new ImageResponse(
    (
      <div style={{
        fontSize: 30,
        background: '#007BFF',
        width: '100%',
        height: '100%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        borderRadius: 10,
        fontWeight: 700,
        fontFamily: 'Arial, sans-serif',
      }}>
        E
      </div>
    ),
    { ...size }
  )
}
