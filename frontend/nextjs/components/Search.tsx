// Search.js
import React, { useState, useEffect } from 'react';
import ResearchForm from './Task/ResearchForm';
import Report from './Task/Report';
import AgentLogs from './Task/AgentLogs';
import AccessReport from './Task/AccessReport';
import InputArea from './InputArea';


const Search = () => {
  const [task, setTask] = useState('');
  const [reportType, setReportType] = useState('');
  const [reportSource, setReportSource] = useState('');
  const [agentLogs, setAgentLogs] = useState([]);
  const [report, setReport] = useState('');
  const [accessData, setAccessData] = useState('');
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const { pathname } = window.location;
      
      // Use the NEXT_PUBLIC_BACKEND_URL environment variable if set
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
      
      let protocol, host;
      
      if (backendUrl) {
        // Parse the backendUrl to extract protocol and host
        try {
          const url = new URL(backendUrl);
          protocol = url.protocol;
          host = url.host;
        } catch (error) {
          console.error('Invalid NEXT_PUBLIC_BACKEND_URL:', backendUrl);
          // Fallback to default behavior if URL is invalid
          protocol = window.location.protocol;
          host = window.location.host;
        }
      } else {
        // Fallback to original logic if environment variable is not set
        protocol = window.location.protocol;
        host = window.location.host;
        host = host.includes('localhost') ? 'localhost:8000' : host;
      }
      
      const ws_protocol = protocol === 'https:' ? 'wss:' : 'ws:';
      const ws_uri = `${ws_protocol}//${host}${pathname}ws`;
      
      const newSocket = new WebSocket(ws_uri);
      setSocket(newSocket);

      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'agentLogs') {
          setAgentLogs((prevLogs) => [...prevLogs, data.output]);
        } else if (data.type === 'report') {
          setReport(data.output);
        } else if (data.type === 'accessData') {
          setAccessData(data.output);
        }
      };

      return () => newSocket.close();
    }
  }, []);

  const handleFormSubmit = (task, reportType, reportSource) => {
    setTask(task);
    setReportType(reportType);
    setReportSource(reportSource);
    // Send data to WebSocket server if needed
    let data = "start " + JSON.stringify({ task: task.value, report_type: reportType.value, report_source: reportSource.value });
    socket.send(data);
  };

  return (
    <div>
      
      <ResearchForm onFormSubmit={handleFormSubmit} defaultReportType="multi_agents"/>
      
      <AgentLogs agentLogs={agentLogs} />
      <Report report={report} />
      <AccessReport accessData={accessData} />
    </div>
  );
};

export default Search;