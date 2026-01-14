import VideoStream from './VideoStream'

function App() {
  return (
    // We remove the inner styling here because VideoStream handles the full page layout now
    <div style={{ margin: 0, padding: 0 }}>
      <VideoStream />
    </div>
  )
}

export default App