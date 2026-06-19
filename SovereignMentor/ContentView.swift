import SwiftUI

struct ContentView: View {
    @State private var isActive = false
    @State private var status = "Sovereign Mentor Ready"
    
    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()
            
            VStack(spacing: 40) {
                Text("ARA")
                    .font(.system(size: 48, weight: .black))
                    .foregroundColor(.white)
                
                Text("SOVEREIGN MENTOR")
                    .font(.system(size: 14, weight: .medium))
                    .tracking(6)
                    .foregroundColor(.gray)
                
                Spacer()
                
                Text(status)
                    .font(.title2)
                    .foregroundColor(isActive ? .green : .white)
                
                Button {
                    isActive.toggle()
                    status = isActive ? "Voice Session Active" : "Sovereign Mentor Ready"
                } label: {
                    Text(isActive ? "END SESSION" : "ACTIVATE MENTOR")
                        .font(.title2.bold())
                        .foregroundColor(.black)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(isActive ? Color.red : Color.white)
                        .cornerRadius(16)
                }
                .padding(.horizontal, 40)
                
                Spacer()
            }
        }
    }
}
