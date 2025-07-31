import React, { useState, useEffect } from 'react';

interface DataEditorProps {
  data: Record<string, any>[];
  columns: string[];
  onChange: (newData: Record<string, any>[]) => void;
}

export function DataEditor({ data, columns, onChange }: DataEditorProps) {
  const [editableData, setEditableData] = useState<Record<string, any>[]>([]);
  const [editingCell, setEditingCell] = useState<{row: number, column: string} | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [searchTerm, setSearchTerm] = useState('');

  // Initialize editable data when props change
  useEffect(() => {
    setEditableData([...data]);
  }, [data]);

  // Filter data based on search term
  const filteredData = React.useMemo(() => {
    if (!searchTerm) return editableData;
    
    return editableData.filter(row =>
      columns.some(column => {
        const value = row[column];
        if (value == null) return false;
        return String(value).toLowerCase().includes(searchTerm.toLowerCase());
      })
    );
  }, [editableData, columns, searchTerm]);

  // Calculate pagination
  const totalPages = Math.ceil(filteredData.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedData = filteredData.slice(startIndex, endIndex);

  const handleCellEdit = (rowIndex: number, column: string, newValue: string) => {
    const actualRowIndex = editableData.indexOf(filteredData[rowIndex]);
    if (actualRowIndex === -1) return;

    const newData = [...editableData];
    newData[actualRowIndex] = {
      ...newData[actualRowIndex],
      [column]: newValue
    };
    
    setEditableData(newData);
    onChange(newData);
  };

  const handleKeyDown = (e: React.KeyboardEvent, rowIndex: number, column: string) => {
    if (e.key === 'Enter') {
      setEditingCell(null);
    } else if (e.key === 'Escape') {
      setEditingCell(null);
    } else if (e.key === 'Tab') {
      e.preventDefault();
      const columnIndex = columns.indexOf(column);
      if (e.shiftKey) {
        // Previous cell
        if (columnIndex > 0) {
          setEditingCell({ row: rowIndex, column: columns[columnIndex - 1] });
        } else if (rowIndex > 0) {
          setEditingCell({ row: rowIndex - 1, column: columns[columns.length - 1] });
        }
      } else {
        // Next cell
        if (columnIndex < columns.length - 1) {
          setEditingCell({ row: rowIndex, column: columns[columnIndex + 1] });
        } else if (rowIndex < paginatedData.length - 1) {
          setEditingCell({ row: rowIndex + 1, column: columns[0] });
        }
      }
    }
  };

  const addNewRow = () => {
    const newRow: Record<string, any> = {};
    columns.forEach(column => {
      newRow[column] = '';
    });
    
    const newData = [...editableData, newRow];
    setEditableData(newData);
    onChange(newData);
  };

  const deleteRow = (rowIndex: number) => {
    const actualRowIndex = editableData.indexOf(filteredData[rowIndex]);
    if (actualRowIndex === -1) return;

    const newData = editableData.filter((_, index) => index !== actualRowIndex);
    setEditableData(newData);
    onChange(newData);
  };

  const formatCellValue = (value: any): string => {
    if (value == null) return '';
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Header with controls */}
      <div className="px-6 py-4 border-b border-gray-200 bg-blue-50">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Data Editor</h3>
          <div className="flex items-center space-x-4">
            <button
              onClick={addNewRow}
              className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              Add Row
            </button>
          </div>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-600">
            Editing {filteredData.length} records • Click any cell to edit
          </div>
          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder="Search data..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <label className="text-sm text-gray-600">
              Rows per page:
              <select
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  setCurrentPage(1);
                }}
                className="ml-2 border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
              </select>
            </label>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                Actions
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200">
                #
              </th>
              {columns.map((column) => (
                <th
                  key={column}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((row, index) => (
              <tr key={startIndex + index} className="hover:bg-gray-50">
                <td className="px-4 py-2 text-sm border-r border-gray-200">
                  <button
                    onClick={() => deleteRow(index)}
                    title="Delete row"
                    className="text-red-500 hover:text-red-700 focus:outline-none"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </td>
                <td className="px-4 py-2 text-sm text-gray-500 border-r border-gray-200 font-medium">
                  {startIndex + index + 1}
                </td>
                {columns.map((column) => {
                  const isEditing = editingCell?.row === index && editingCell?.column === column;
                  const cellValue = formatCellValue(row[column]);
                  
                  return (
                    <td
                      key={column}
                      className="px-4 py-2 text-sm border-r border-gray-200 relative"
                    >
                      {isEditing ? (
                        <input
                          type="text"
                          value={cellValue}
                          onChange={(e) => handleCellEdit(index, column, e.target.value)}
                          onBlur={() => setEditingCell(null)}
                          onKeyDown={(e) => handleKeyDown(e, index, column)}
                          className="w-full px-2 py-1 border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-blue-50"
                          autoFocus
                        />
                      ) : (
                        <div
                          onClick={() => setEditingCell({ row: index, column })}
                          className="min-h-[24px] cursor-text hover:bg-blue-50 px-2 py-1 rounded -mx-2 -my-1 max-w-xs truncate"
                          title={cellValue}
                        >
                          {cellValue || <span className="text-gray-400 italic">Empty</span>}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                First
              </button>
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <span className="px-3 py-1 text-sm text-gray-600">
                {currentPage} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Last
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Help text */}
      <div className="px-6 py-3 border-t border-gray-200 bg-yellow-50">
        <p className="text-sm text-yellow-800">
          💡 Tips: Click any cell to edit • Use Tab/Shift+Tab to navigate • Press Enter or click outside to save changes
        </p>
      </div>

      {/* Empty state */}
      {filteredData.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data</h3>
          <p className="text-gray-600 mb-4">
            {searchTerm ? 'No records match your search.' : 'This block contains no data records.'}
          </p>
          {!searchTerm && (
            <button
              onClick={addNewRow}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Add First Row
            </button>
          )}
        </div>
      )}
    </div>
  );
}